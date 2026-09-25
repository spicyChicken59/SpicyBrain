import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import type { TeachingModule, TeachingVisual } from "../src/teaching-schema";
import type {
  Claim,
  CourseConcept,
  Lesson,
  Scenario,
  Source,
} from "../src/content-schema";

// Regression tests for the product-claim corrections of 25 September 2026
// (commit "Correct fourteen modules' product claims against pinned primary
// sources"). Each correction replaced a sentence that a pinned primary source
// contradicted. The tests below are written from the FINDING, not from the
// corrected sentence: a forbidding pattern describes what was wrong, so the
// usual rewordings of the old claim are caught too, and it is kept tight
// enough not to match the corrected text, a negated statement of it, or
// unrelated teaching. A phrase pattern cannot catch every paraphrase; each was
// checked against same-meaning rewordings and negated near-misses.
//
// Surfaces: every string of the teaching JSON, the course package JSON, the
// lesson JSON and every section of the lesson Markdown. Four narrow
// exemptions keep the evidence honest without hiding teaching:
// - a beat's `changeNote` narrates what was replaced, so it may name the
//   retired wording;
// - a source record may quote its primary source verbatim, so passages in
//   single quotes inside `sources[...]` are the evidence, not the teaching;
// - a source record may say what the module no longer claims ("the claim
//   that ...", "its statement that ...", "no longer teaches that ...", "to
//   correct the ..."); that span is a retraction;
// - a source record whose caveat declares part of its source "not relied
//   on" keeps its reviewedEvidence as the record of what that source says.
// The record's own words around them are still searched, because several
// corrections changed a source record's summary or caveat. The qualifier
// checks (requireQualifier) read teaching only: a source record describes
// one source's own statement, which is an attribution by construction.

type Leaf = { where: string; text: string; source: boolean };

interface ModulePackage {
  claims: Claim[];
  concepts: CourseConcept[];
  scenarios: Scenario[];
  sources: Source[];
}

interface ModuleFiles {
  name: string;
  teaching: TeachingModule;
  pkg: ModulePackage;
  lesson: Lesson;
  md: Map<string, string>;
  /** Teaching surfaces searched by the forbidding checks. */
  leaves: Leaf[];
  /** Every string, change notes and quotations included. */
  allLeaves: Leaf[];
}

const moduleNames = [
  "identity",
  "aws",
  "azure",
  "gcp",
  "ai-platform",
  "operations",
  "genai-eval",
  "delta-writes",
  "apps",
  "bi",
  "sharing",
  "serving",
  "retrieval",
  "tools",
] as const;
type ModuleName = (typeof moduleNames)[number];

const pathsOf = (name: ModuleName) => ({
  teaching: `content/teaching/dbxfe/dbxfe-${name}.json`,
  pkg: `content/courses/dbxfe/modules/dbxfe-${name}.json`,
  lesson: `content/courses/dbxfe/lessons/dbxfe-${name}-l01.json`,
  md: `content/courses/dbxfe/lessons/dbxfe-${name}-l01.md`,
});

// A single-quoted passage opens after whitespace, "(", ":" or "[", may
// contain an apostrophe followed by a letter (workspace's), and closes before
// whitespace, punctuation or the end.
const quotedPassage = /(^|[\s(:[])'(?:[^']|'(?=[A-Za-z]))*'(?=$|[\s.,;:)\]])/g;
// A retraction a source record states, up to the end of its clause.
const retraction =
  /\b(?:the claim that|statement that|no longer (?:teaches|says|states)(?: that)?|to correct the)\b[^.;]*/gi;

function collect(
  value: unknown,
  where: string,
  out: Leaf[],
  authored: boolean,
): void {
  if (typeof value === "string") {
    const source = where.includes(".sources[");
    const text =
      authored && source
        ? value
            .replace(quotedPassage, "$1[quoted]")
            .replace(retraction, "[retracted]")
        : value;
    out.push({ where, text, source });
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item: unknown, index) => {
      const key =
        item && typeof item === "object" && "id" in item
          ? String((item as { id: unknown }).id)
          : String(index);
      collect(item, `${where}[${key}]`, out, authored);
    });
    return;
  }
  if (value && typeof value === "object")
    for (const [key, item] of Object.entries(value))
      if (!(authored && key === "changeNote"))
        collect(item, `${where}.${key}`, out, authored);
}

function sectionsOf(md: string): Map<string, string> {
  const parts = md.split(/<!-- section:([a-z0-9-]+) -->/);
  const out = new Map<string, string>();
  for (let i = 1; i < parts.length; i += 2) out.set(parts[i], parts[i + 1]);
  return out;
}

async function load(name: ModuleName): Promise<ModuleFiles> {
  const p = pathsOf(name);
  const [teachingText, pkgText, lessonText, mdText] = await Promise.all([
    readFile(p.teaching, "utf8"),
    readFile(p.pkg, "utf8"),
    readFile(p.lesson, "utf8"),
    readFile(p.md, "utf8"),
  ]);
  const teaching = JSON.parse(teachingText) as TeachingModule;
  const pkg = JSON.parse(pkgText) as ModulePackage;
  const lesson = JSON.parse(lessonText) as Lesson;
  const md = sectionsOf(mdText);
  const leaves: Leaf[] = [];
  const allLeaves: Leaf[] = [];
  for (const authored of [true, false]) {
    const out = authored ? leaves : allLeaves;
    collect(teaching, "teaching", out, authored);
    collect(pkg, "package", out, authored);
    collect(lesson, "lesson", out, authored);
    for (const [id, body] of md)
      out.push({ where: `md#${id}`, text: body, source: false });
  }
  const disclaimed = new Set(
    allLeaves
      .filter(
        (l) => l.where.endsWith(".caveat") && /\bnot relied on\b/.test(l.text),
      )
      .map((l) => l.where.replace(/\.caveat$/, ".reviewedEvidence")),
  );
  return {
    name,
    teaching,
    pkg,
    lesson,
    md,
    leaves: leaves.filter((l) => !(l.source && disclaimed.has(l.where))),
    allLeaves,
  };
}

const files = Object.fromEntries(
  await Promise.all(moduleNames.map(async (n) => [n, await load(n)] as const)),
) as Record<ModuleName, ModuleFiles>;

const excerpt = (text: string, at: number) =>
  text
    .slice(Math.max(0, at - 70), at + 90)
    .replace(/\s+/g, " ")
    .trim();

/** The finding's wrong assertion must not appear on any surface. */
function forbid(m: ModuleFiles, pattern: RegExp, finding: string): void {
  assert.ok(!pattern.global, "forbid() patterns are not global");
  const hits = m.leaves.flatMap((leaf) => {
    const hit = pattern.exec(leaf.text);
    return hit ? [`${leaf.where}: …${excerpt(leaf.text, hit.index)}…`] : [];
  });
  assert.deepEqual(hits, [], `dbxfe-${m.name}: ${finding}`);
}

// Clause: split at sentence ends, semicolons, colons, line breaks, table
// cell bars and the text equivalents' em-dash separators.
const CLAUSE = /(?<=[.;:!?])\s+|\n+|\s[|—]\s/;
// Sentence: the same without semicolons and colons.
const SENTENCE = /(?<=[.!?])\s+|\n+|\s[|—]\s/;

/**
 * Wherever a clause makes the assertion the finding narrowed (`trigger`), it
 * must also carry the qualifier the primary source requires.
 */
function requireQualifier(
  m: ModuleFiles,
  trigger: RegExp[],
  qualifier: RegExp,
  finding: string,
  unit: RegExp = CLAUSE,
): void {
  const hits = m.leaves
    .filter((leaf) => !leaf.source)
    .flatMap((leaf) =>
      leaf.text
        .split(unit)
        .filter((c) => trigger.every((t) => t.test(c)) && !qualifier.test(c))
        .map(
          (c) =>
            `${leaf.where}: ${c.replace(/\s+/g, " ").trim().slice(0, 220)}`,
        ),
    );
  assert.deepEqual(hits, [], `dbxfe-${m.name}: ${finding}`);
}

function byId<T extends { id: string }>(items: T[], id: string): T {
  const found = items.find((item) => item.id === id);
  assert.ok(found, `${id} exists`);
  return found;
}
const beat = (m: ModuleFiles, id: string) => byId(m.teaching.beats, id);
const claim = (m: ModuleFiles, id: string) => byId(m.teaching.claims, id);
const pkgClaim = (m: ModuleFiles, id: string) => byId(m.pkg.claims, id);
const concept = (m: ModuleFiles, id: string) => byId(m.teaching.concepts, id);
const pkgConcept = (m: ModuleFiles, id: string) => byId(m.pkg.concepts, id);
const visual = (m: ModuleFiles, id: string) => byId(m.teaching.visuals, id);
const extension = (m: ModuleFiles, id: string) =>
  byId(m.teaching.extensionCards, id);
const selfCheck = (m: ModuleFiles, id: string) =>
  byId(m.teaching.selfQuestions, id);
const card = (m: ModuleFiles, id: string) => byId(m.lesson.cards, id);
const optionOf = (
  questions: { id: string; options: { id: string; rationale: string }[] }[],
  questionId: string,
  optionId: string,
) => byId(byId(questions, questionId).options, optionId);
function section(m: ModuleFiles, id: string): string {
  const body = m.md.get(id);
  assert.ok(body, `${id} section exists`);
  return body;
}

/** A corrected beat moved off its first published version. */
function beatMoved(m: ModuleFiles, ...ids: string[]) {
  for (const id of ids)
    assert.notEqual(beat(m, id).version, "1.0.0", `${id} version moved`);
}
/** A lesson whose Markdown or cards changed moved its content version. */
function lessonMoved(m: ModuleFiles, from = "1.0.0") {
  assert.notEqual(
    m.lesson.contentVersion,
    from,
    `${m.lesson.id} contentVersion moved`,
  );
}

// ---------------------------------------------------------------------------
// dbxfe-identity
// ---------------------------------------------------------------------------

test("identity: the SDK is not said to refresh an M2M token 40 seconds before expiry", () => {
  // Source: databricks-sdk-py 9df82c7 databricks/sdk/oauth.py (Refreshable,
  // _MAX_STALE_DURATION): by default a token goes stale min(TTL/2, 20 min)
  // before expiry and a request starts a background refresh; the 40 s margin
  // only decides when a request blocks.
  const m = files.identity;
  forbid(
    m,
    /\b40 ?(?:seconds|s)\b[^.]{0,20}\b(?:before|ahead of|prior to|from)\b[^.]{0,25}\bexpir/i,
    "40 seconds before expiry is the blocking margin, not when the SDK refreshes",
  );
  const handbook = beat(m, "dbxfe-identity-m2m").handbook.markdown;
  assert.match(handbook, /final 20 minutes/);
  assert.match(handbook, /starts a background refresh/);
  assert.match(
    handbook,
    /within 40 seconds of expiry[^.]*waits for a new token/,
  );
  beatMoved(m, "dbxfe-identity-m2m");
});

test("identity: the provider and the SDK are not said to agree on what an ABAC condition tests", () => {
  // Sources: terraform-provider-databricks f745277 docs/resources/policy_info.md
  // ("conditions on governance tags and the user identity") and
  // databricks-sdk-py 9df82c7 service/catalog.py PoliciesAPI ("securable
  // properties, governance tags, and environment contexts").
  const m = files.identity;
  forbid(
    m,
    /\bagree\b[^.]{0,80}\bconditions?\b/i,
    "the two sources name different condition inputs",
  );
  forbid(
    m,
    /\bconditions\b[^.]{0,20}\bgovernance tags and the caller's identity\b/i,
    "the SDK's list includes securable properties and environment contexts",
  );
  // A clause that says what a condition tests from BOTH sources keeps the
  // SDK's wider list or the attribution to the provider.
  requireQualifier(
    m,
    [/\bconditions?\b/i, /\bgovernance tags\b/i, /\b(?:both|same|agree)\w*/i],
    /\bsecurable properties\b|\benvironment contexts\b|\bprovider's words\b/i,
    "a clause giving one list of condition inputs for both sources names the SDK's",
  );
  const handbook = beat(m, "dbxfe-identity-abac").handbook.markdown;
  assert.match(handbook, /governance tags and the user identity/);
  assert.match(
    handbook,
    /securable properties, governance tags and environment contexts/,
  );
  beatMoved(m, "dbxfe-identity-abac");
});

test("identity: an account admin is not taught as the only caller who enables a system schema", () => {
  // Source: databricks-sdk-py 9df82c7 service/catalog.py
  // SystemSchemasAPI.enable: "The caller must be an account admin or a
  // metastore admin." The provider's account-admin wording may stay only as
  // the provider's, attributed.
  const m = files.identity;
  requireQualifier(
    m,
    [
      /\b(?:enabl\w*|turn\w* on|switch\w* on)/i,
      /\baccount admin(?:istrator)?s?\b/i,
      /\b(?:system|schema)/i,
    ],
    /\bmetastore admin|\bprovider documents\b/i,
    "a sentence naming who enables a system schema also names the metastore admin",
  );
  const both = /\baccount admin or a metastore admin\b/;
  assert.match(claim(m, "dbxfe-identity-claim-audit").description, both);
  assert.match(
    claim(m, "dbxfe-identity-claim-ext-system-schema").description,
    both,
  );
  assert.match(
    pkgClaim(m, "dbxfe-identity-course-claim-audit").description,
    both,
  );
  assert.match(
    pkgClaim(m, "dbxfe-identity-course-claim-ext-system-schema").description,
    both,
  );
  assert.match(beat(m, "dbxfe-identity-audit").explanation, both);
  assert.match(
    extension(m, "dbxfe-identity-extension-system-schema").answer,
    both,
  );
  assert.match(
    concept(m, "dbxfe-identity-extension-system-schema-concept").definition,
    both,
  );
  assert.match(section(m, "dbxfe-identity-l01-audit"), both);
  beatMoved(m, "dbxfe-identity-audit");
  assert.equal(
    extension(m, "dbxfe-identity-extension-system-schema").revision,
    "2",
  );
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-aws
// ---------------------------------------------------------------------------

test("aws: secure cluster connectivity is not taught as needing no inbound rule at all", () => {
  // Sources: terraform-provider-databricks b1d7b85
  // docs/guides/aws-e2-firewall-workspace.md (ingress: "Allow TCP/UDP on all
  // ports when the traffic source uses the same security group") and
  // databricks-sdk-py 9df82c7 service/provisioning.py. Only inbound rules from
  // OTHER sources are irrelevant to reaching the relay.
  const m = files.aws;
  requireQualifier(
    m,
    [
      /\binbound\b/i,
      /\b(?:no|not|never|nothing|none|drop out|irrelevant|unnecessary|(?:do|does|is|are)n't)\b/i,
    ],
    /\bsame[- ](?:security[- ])?group\b|\boutside\b|\bother sources?\b|\banother source\b|\banywhere else\b|\b(?:no|any) other\b|\bother inbound\b/i,
    "a clause that dismisses inbound rules keeps the same-group exception",
  );
  forbid(
    m,
    /\bonly (?:on )?(?:the )?outbound\b|(?<!initiates )\boutbound[- ]only\b|\boutbound side only\b|\bdepends only on the outbound\b|\bnothing connects in\b/i,
    "the security group's same-group inbound rules are required too (a node still INITIATES outbound only)",
  );
  assert.match(
    beat(m, "dbxfe-aws-vpc").handbook.markdown,
    /inbound TCP and UDP on all ports from the same security group/,
  );
  assert.match(
    claim(m, "dbxfe-aws-claim-vpc").description,
    /inbound TCP and UDP from the same group/,
  );
  assert.match(
    section(m, "dbxfe-aws-l01-classic"),
    /inbound TCP and UDP from the same group/,
  );
  assert.match(
    card(m, "dbxfe-aws-l01-card4").answer,
    /same-group inbound rules/,
  );
  beatMoved(m, "dbxfe-aws-vpc");
  assert.equal(selfCheck(m, "dbxfe-aws-vpc-self").revision, "2");
  assert.equal(card(m, "dbxfe-aws-l01-card4").revision, "2");
  lessonMoved(m);
});

test("aws: instance profiles are not taught as classic-only or absent from serverless", () => {
  // Sources: terraform-provider-databricks b1d7b85
  // docs/resources/instance_profile.md and sql_global_config.md;
  // databricks-sdk-py 9df82c7 service/compute.py and service/sql.py (instance
  // profiles for Databricks SQL Serverless; the workspace SQL warehouse
  // instance_profile_arn, also applied to serverless notebooks and jobs).
  const m = files.aws;
  forbid(
    m,
    /(?<!\bnot (?:strictly )?)\bclassic(?:[- ](?:compute|clusters?|nodes?))?[- ]only\b|\bonly (?:on |for |with )?classic(?: compute)?\b[^.;]{0,40}\binstance profiles?\b|\binstance profiles?\b[^.;]{0,40}\bonly (?:on|for|with|to) classic\b/i,
    "the API reference documents instance profiles for SQL Serverless",
  );
  forbid(
    m,
    /\bserverless\b[^.;]{0,40}\b(?:cannot|can't|does not|doesn't|never) (?:use|have|carry|take)s? (?:an? )?instance profiles?\b(?![^.;]{0,60}\b(?:unless|except|other than)\b)/i,
    "serverless can use a workspace instance profile",
  );
  forbid(m, /\binstance profiles? belongs? to classic\b/i, "not classic-only");
  forbid(
    m,
    /\bno (?:EC2 )?instance to carry a role\b/i,
    "serverless can still use a workspace instance profile",
  );
  forbid(
    m,
    /\bstorage credential only\b/i,
    "not the only serverless storage identity",
  );
  forbid(m, /\bonly storage path\b/i, "not the only serverless storage path");
  forbid(
    m,
    /\bno instance profile(?= to name|[.,;)])/i,
    "serverless is not stated to have no instance profile",
  );
  forbid(
    m,
    /\band the instance profile\.\s+(?:Appearing|Unchanged)\b/,
    "the instance profile leaves only once no workspace SQL warehouse setting names it",
  );
  const profile = beat(m, "dbxfe-aws-profile").handbook.markdown;
  assert.match(profile, /instance_profile_arn/);
  assert.match(profile, /Databricks SQL Serverless/);
  assert.match(profile, /serverless compute for notebooks\s+and jobs/);
  assert.match(claim(m, "dbxfe-aws-claim-profile").context, /SQL Serverless/);
  assert.match(
    pkgClaim(m, "dbxfe-aws-course-claim-profile").context,
    /SQL Serverless/,
  );
  const provision = byId(
    visual(m, "dbxfe-aws-responsibilities-visual").states,
    "provision",
  ).table!.rows.find((row) => row[0] === "Storage identity");
  assert.match(
    provision![2],
    /instance profile set in the workspace's SQL warehouse configuration/,
  );
  assert.match(
    section(m, "dbxfe-aws-l01-storage"),
    /Databricks SQL Serverless/,
  );
  beatMoved(m, "dbxfe-aws-profile", "dbxfe-aws-responsibilities");
  assert.equal(selfCheck(m, "dbxfe-aws-responsibilities-self").revision, "2");
  assert.equal(
    extension(m, "dbxfe-aws-extension-bucket-condition").revision,
    "2",
  );
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-azure
// ---------------------------------------------------------------------------

test("azure: only a classic workspace is taught to bring a managed resource group", () => {
  // Source: Azure/azure-rest-api-specs 2094b1c Microsoft.Databricks
  // stable/2026-01-01/openapi.json: the Serverless compute mode does not
  // accept a managed resource group.
  // The wrong assertion has a GENERIC subject (a workspace, the workspace,
  // creating a workspace); sentences about Cinderline's own workspace
  // dbw-cinderline-prod, which is classic in the scenario, are not it.
  const m = files.azure;
  const generic =
    "(?:[Aa]n?|[Tt]he) (?!classic\\b)(?:Azure )?(?:Databricks )?workspace";
  for (const [pattern, finding] of [
    [
      new RegExp(
        `\\b[Cc]reating ${generic}\\b[^.;]{0,120}?\\bprovisions? (?:a|a second)\\b`,
      ),
      "creating a workspace is not said to provision a managed resource group",
    ],
    [
      new RegExp(
        `\\b(?:[Cc]reat(?:e|es|ed)|[Dd]eploy(?:ing|s|ed)?) (?:${generic}|(?:any|every) (?!classic\\b)(?:Azure )?(?:Databricks )?workspace)\\b[^.;]{0,120}?\\b(?:provisions?|creates?|adds?)\\b[^.;]{0,30}\\bmanaged resource group\\b`,
      ),
      "creating a workspace is not said to provision a managed resource group",
    ],
    [
      /\b(?:[Ee]very|[Aa]ny|[Aa]ll) (?!classic\b)(?:Azure )?Databricks workspaces?\b[^.;]{0,40}\b(?:comes? with|ha(?:s|ve)|gets?|brings?)\b[^.;]{0,30}\bmanaged resource groups?\b/,
      "no workspace in general is said to come with a managed resource group",
    ],
    [
      new RegExp(
        `\\b${generic} (?:resource )?is (?:itself )?an Azure resource with a locked\\b`,
      ),
      "a workspace is not said to be a resource with a locked managed group",
    ],
    [
      new RegExp(
        `\\b${generic} resource (?:comes )?with a (?:locked managed )?resource group\\b`,
      ),
      "a workspace resource is not said to come with a resource group",
    ],
    [
      new RegExp(`\\bprovisions with ${generic}\\b`),
      "the managed group is not said to come with any workspace",
    ],
    [
      /(?:^|— )An Azure resource with a locked managed resource group\b/,
      "the comparison row names the classic workspace",
    ],
    [
      /\b(?:[Tt]he workspace|On Azure,? it) is a resource\b/,
      "the resource that brings a managed group is the classic workspace",
    ],
  ] as const)
    forbid(m, pattern, `${finding}: the Serverless compute mode accepts none`);
  const serverless =
    /Serverless compute mode does not accept a managed resource group/;
  assert.match(claim(m, "dbxfe-azure-claim-workspace").description, serverless);
  assert.match(beat(m, "dbxfe-azure-account").handbook.markdown, serverless);
  assert.match(card(m, "dbxfe-azure-l01-card1").prompt, /\bclassic\b/);
  beatMoved(m, "dbxfe-azure-account", "dbxfe-azure-aws");
  assert.equal(card(m, "dbxfe-azure-l01-card1").revision, "2");
  lessonMoved(m);
});

test("azure: the access connector's managed identity is not said never to become a Databricks principal", () => {
  // Source: terraform-provider-databricks b1d7b85 docs/index.md (Azure
  // managed identity authentication). The module can say only that this
  // identity is not provisioned here and is used through the storage
  // credential.
  const m = files.azure;
  // The categorical "never" is what the provider contradicts; "not a
  // Databricks principal" in THIS design (the handbook's table, the
  // question's option D) is scenario-bound and was kept by the decision.
  forbid(
    m,
    /\bmanaged identity\b[^.;|]{0,40}\b(?:never|cannot|can't|could not|will not|won't)\b[^.;|]{0,20}\b(?:becomes?|be)\b[^.;|]{0,10}\bDatabricks principal\b|\bmanaged identity\b[^.;|]{0,40}\bnever\b|\bNever: not a Databricks principal\b/i,
    "a managed identity added through databricks_service_principal is a Databricks principal",
  );
  const identity = visual(m, "dbxfe-azure-identity-visual");
  assert.match(
    identity.caption,
    /not provisioned here and is used only through the storage credential/,
  );
  beatMoved(m, "dbxfe-azure-identity");
});

test("azure: a firewall route is not an explicit outbound method for Internet-next-hop routes in a private subnet", () => {
  // Sources: MicrosoftDocs/azure-docs 194fd50
  // articles/virtual-network/ip-services/default-outbound-access.md and
  // subnet-delegation-overview.md.
  // Azure's general statement that virtual machines in private subnets need
  // an explicit method (the outbound claim) stays; what was wrong is applying
  // it to the injected workspace as if the firewall route were enough.
  const m = files.azure;
  forbid(
    m,
    /\b(?:injected|workspace subnets?)\b[^.]{0,120}\b(?:NAT gateway or a (?:route to a )?firewall|(?:route to a )?firewall or a NAT gateway)\b|\b(?:NAT gateway or a (?:route to a )?firewall|(?:route to a )?firewall or a NAT gateway)\b[^.]{0,80}\binjected\b/i,
    "the firewall route does not carry Internet-next-hop service-tag traffic",
  );
  forbid(
    m,
    /\bretired\b[^.]{0,60}\bdefault outbound\b/i,
    "default outbound changed for new networks; it was not retired",
  );
  forbid(
    m,
    /\bdefaultOutboundAccess set to false(?! unless| by default)/,
    "false by default, unless configured otherwise",
  );
  forbid(
    m,
    /\bprivate (?:subnets )?by default, so an (?:explicit outbound method is required|injected workspace)\b/i,
    "private-by-default does not reach delegated subnets, and the consequence is the Internet-next-hop routes",
  );
  const routes = beat(m, "dbxfe-azure-routes").handbook.markdown;
  assert.match(
    routes,
    /next hop Internet[^.]*fails unless an explicit outbound method/,
  );
  assert.match(routes, /delegated subnets/);
  assert.match(
    section(m, "dbxfe-azure-l01-patterns"),
    /next hop is Internet fails unless an explicit outbound method/,
  );
  const outbound = extension(m, "dbxfe-azure-extension-default-outbound");
  assert.match(outbound.explanation, /unless configured otherwise/);
  assert.match(outbound.explanation, /delegated subnets/);
  beatMoved(m, "dbxfe-azure-routes");
  lessonMoved(m);
});

test("azure: the data role assignment is not the only Azure permission in the connector chain", () => {
  // Source: terraform-provider-databricks b1d7b85 docs/guides/unity-catalog-azure.md
  // (the connector's identity also gets Storage Account Contributor, Storage
  // Queue Data Contributor and EventGrid EventSubscription Contributor).
  const m = files.azure;
  forbid(
    m,
    /\b(?:only|sole|single)\b[^.;]{0,30}\bAzure permission\b/i,
    "the Terraform guide assigns further roles to the connector's identity",
  );
  const handbook = beat(m, "dbxfe-azure-connector").handbook.markdown;
  assert.match(handbook, /Storage Account Contributor/);
  assert.match(handbook, /Storage Queue Data Contributor/);
  assert.match(handbook, /EventGrid EventSubscription Contributor/);
  beatMoved(m, "dbxfe-azure-connector");
});

test("azure: the workspace firewall is not said to create its access connector", () => {
  // Sources: Microsoft.Databricks openapi.json (2094b1c) and
  // hashicorp/terraform-provider-azurerm bfc2300
  // website/docs/r/databricks_workspace.html.markdown: the connector is one
  // associated with the workspace.
  const m = files.azure;
  forbid(
    m,
    /\baccess connector\b[^.;]{0,20}\b(?:it|the workspace) creates\b|\b(?:it|the workspace) creates (?:its own |an |the )?access connector\b|\baccess connector (?:that is )?created (?:by|with) the workspace\b/i,
    "the connector is associated with the workspace, not created by it",
  );
  const associated = /access connector associated with the workspace/;
  assert.match(
    extension(m, "dbxfe-azure-extension-workspace-firewall").answer,
    associated,
  );
  assert.match(claim(m, "dbxfe-azure-claim-firewall").description, associated);
  assert.match(
    concept(m, "dbxfe-azure-extension-workspace-firewall-concept").definition,
    associated,
  );
  assert.equal(
    extension(m, "dbxfe-azure-extension-workspace-firewall").revision,
    "2",
  );
});

test("azure: a linked dfs zone does not answer every dfs name", () => {
  // Source: MicrosoftDocs/azure-docs 194fd50
  // articles/private-link/private-endpoint-dns.md: only names whose CNAME
  // points into the privatelink namespace are answered by the linked zone.
  const m = files.azure;
  forbid(
    m,
    /\b(?:every|all|any) dfs names? (?:is |are |gets? )?(?:answered|resolved|resolves?)\b/i,
    "only CNAMEs into the privatelink namespace reach the zone",
  );
  assert.match(
    extension(m, "dbxfe-azure-extension-dns-fallback").explanation,
    /dfs name whose CNAME points into the privatelink namespace is answered there/,
  );
});

// ---------------------------------------------------------------------------
// dbxfe-gcp
// ---------------------------------------------------------------------------

test("gcp: account APIs are not taught to accept only Google-issued OIDC tokens", () => {
  // Sources: terraform-provider-databricks f745277 docs/index.md,
  // docs/resources/mws_networks.md and mws_vpc_endpoint.md: only creating or
  // updating workspaces, network configurations and VPC endpoints needs a
  // Google-issued OIDC token.
  const m = files.gcp;
  forbid(
    m,
    /\bonly Google-issued OIDC tokens?\b[^.;]{0,30}\baccount(?:-level)? APIs?\b|\bAPIs? accepts? only Google-issued OIDC\b|\baccount(?:-level)? APIs?\b[^.;]{0,25}\b(?:only )?(?:accepts?|takes?|requires?|needs?|uses?) (?:only )?(?:an? )?Google-issued OIDC\b/i,
    "other account API calls take a Databricks OAuth token",
  );
  forbid(
    m,
    /\baccount(?:-level)? APIs\b[^;]{0,60}?\b(?:only|with)\b[^;.]{0,20}\bGoogle-issued OIDC\b/i,
    "the OIDC requirement is scoped to three resource operations",
  );
  assert.match(
    beat(m, "dbxfe-gcp-accounts").handbook.markdown,
    /\b[Cc]reating or updating\b[^.]*\bworkspace\b[^.]*\bnetwork configuration\b[^.]*\bVPC endpoint\b[^.]*\bGoogle-issued OIDC token rather than a Databricks OAuth token\b/,
  );
  assert.match(
    claim(m, "dbxfe-gcp-claim-workspace").description,
    /rather than a Databricks OAuth token/,
  );
  assert.match(
    pkgClaim(m, "dbxfe-gcp-course-claim-workspace").description,
    /rather than a Databricks OAuth token/,
  );
  beatMoved(m, "dbxfe-gcp-accounts");
});

test("gcp: the subnet's own ingress rule is not dismissed as never consulted", () => {
  // Source: databricks/terraform-databricks-sra a3403d9
  // gcp/modules/workspace_deployment/vpc-firewall.tf: the intra-subnet
  // ingress rule is pre-created, or Databricks creates it.
  // "Opening ingress rules" as a wrong fix for a timeout stays true; what
  // was wrong is saying no ingress rule is consulted or needed at all.
  const m = files.gcp;
  forbid(
    m,
    /\bingress (?:firewall )?rules? (?:is|are) (?:never|not) (?:ever )?(?:consulted|needed|required)\b|\bno ingress (?:firewall )?rules? (?:is |are )?(?:ever |at all )?(?:consulted|needed|required|matters?)\b|\bingress (?:firewall )?rules? (?:plays?|has|have) no (?:part|role)\b/i,
    "the intra-subnet ingress rule is required and stays in place",
  );
  assert.match(
    selfCheck(m, "dbxfe-gcp-vpc-self").modelAnswer,
    /ingress rule for traffic within the Databricks subnet/,
  );
  assert.equal(selfCheck(m, "dbxfe-gcp-vpc-self").revision, "2");
  beatMoved(m, "dbxfe-gcp-vpc");
});

test("gcp: the customer grants the Databricks key account only on the manual option", () => {
  // Source: databricks-sdk-py 9df82c7 service/provisioning.py (the GCP key
  // service account and its manual grant option).
  const m = files.gcp;
  requireQualifier(
    m,
    [
      /\bgrants? (?:it|the (?:key )?service account)\b[^.;]{0,20}\b(?:use of|access to|permission to use|rights? (?:on|to))\b[^.;]{0,10}\bthe key\b/i,
    ],
    /\bmanual\b/i,
    "the grant is the customer's only when the manual option is set",
  );
  assert.match(
    optionOf(
      m.teaching.questions,
      "dbxfe-gcp-accounts-question",
      "dbxfe-gcp-accounts-question-d",
    ).rationale,
    /\bmanual option\b[^.]*\bgrants it use of the key\b/,
  );
});

test("gcp: a project-level role is not said to widen every Cinderline bucket", () => {
  // Sources: Google policytroubleshooter v1 and storage v1 discovery
  // documents (Bucket.projectNumber): a project role reaches the buckets in
  // that project.
  const m = files.gcp;
  forbid(
    m,
    /\b(?:every|all(?: of)?|each) Cinderline(?:'s)? buckets?\b|\b(?:every|all(?: of)?(?: the)?) buckets? (?:that )?Cinderline (?:owns|has)\b/i,
    "only the buckets in cl-dbx-prod",
  );
  assert.match(
    optionOf(m.lesson.questions, "dbxfe-gcp-l01-q1", "dbxfe-gcp-l01-q1-b")
      .rationale,
    /every bucket in cl-dbx-prod/,
  );
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-ai-platform
// ---------------------------------------------------------------------------

test("ai-platform: one external model per endpoint is not taught as settled", () => {
  // Sources: databricks-sdk-py 9df82c7 service/serving.py (all external
  // models within an endpoint must share one task type) against
  // terraform-provider-databricks f745277 docs/resources/model_serving.md.
  const m = files["ai-platform"];
  forbid(
    m,
    /\bone endpoint per (?:provider |external )?model\b|\bserves only that entity\b|\bsingle served entity\b|\b(?:only|exactly|just) one external model\b|\bone external model per endpoint\b|\beach external model\b[^.;]{0,20}\b(?:its own|a separate|a dedicated) endpoint\b/i,
    "the SDK implies several external models may share an endpoint",
  );
  const handbook = beat(m, "dbxfe-ai-platform-external").handbook.markdown;
  assert.match(
    handbook,
    /all external models within an endpoint must share one task type/,
  );
  assert.match(handbook, /the two artifacts disagree/);
  assert.match(
    claim(m, "dbxfe-ai-platform-claim-external").description,
    /must share one task type/,
  );
  beatMoved(m, "dbxfe-ai-platform-external");
});

test("ai-platform: serving-endpoint AI Gateway settings are not presented as the current AI Gateway", () => {
  // Source: databricks/devhub 35f4745 src/content/docs/agents/ai-gateway.md
  // (the endpoint settings are the previous version of Unity AI Gateway).
  const m = files["ai-platform"];
  forbid(
    m,
    /\b(?:The )?Databricks(?:'s?)? AI Gateway is (?:the )?(?:configuration|settings?)\b/i,
    "the endpoint settings are the previous version of Unity AI Gateway",
  );
  assert.match(
    extension(m, "dbxfe-ai-platform-extension-mlflowgateway").explanation,
    /previous version of Unity AI Gateway/,
  );
});

test("ai-platform: a custom agent's own serving endpoint is not taught as the current path", () => {
  // Sources: databricks/devhub 35f4745 src/content/docs/agents/custom-agents.md
  // and overview.md: run a custom agent in a Databricks App; agents.deploy()
  // to its own Model Serving endpoint is legacy.
  const m = files["ai-platform"];
  forbid(
    m,
    /\bcode hosted on a serving endpoint\b|\ball end at serving endpoints\b|\bModel Serving hosts (?:all|each|every one) of them\b|\bThe agent framework hosts\b/i,
    "the endpoint path is legacy; Databricks recommends a Databricks App",
  );
  requireQualifier(
    m,
    [
      /\bcustom agents?\b/i,
      /\b(?:hosted on|hosts? (?:the|a)? ?(?:custom )?agent|deployed (?:to|with)|deploy\(\)|agents\.deploy)/i,
    ],
    /\blegacy\b|\bDatabricks App\b/i,
    "a sentence on where a custom agent runs names the legacy path or the App",
    SENTENCE,
  );
  const map = beat(m, "dbxfe-ai-platform-map").explanation;
  assert.match(map, /recommends running in a Databricks App/);
  assert.match(map, /legacy path/);
  const description = claim(m, "dbxfe-ai-platform-claim-custom").description;
  assert.match(description, /legacy/);
  assert.match(description, /Databricks App/);
  assert.match(
    pkgClaim(m, "dbxfe-ai-platform-course-claim-custom").description,
    /legacy and recommends running a custom agent in a Databricks App/,
  );
  beatMoved(
    m,
    "dbxfe-ai-platform-map",
    "dbxfe-ai-platform-custom",
    "dbxfe-ai-platform-serving",
  );
  assert.equal(selfCheck(m, "dbxfe-ai-platform-custom-self").revision, "2");
  assert.equal(card(m, "dbxfe-ai-platform-l01-card9").revision, "2");
  lessonMoved(m);
});

test("ai-platform: Agent Bricks is not taught as the name of configured agents only", () => {
  // Source: databricks/devhub 35f4745 src/content/docs/agents/overview.md
  // (Agent Bricks names the whole agent platform, custom Python agents
  // included).
  const m = files["ai-platform"];
  // The unscoped rule ("Agent Bricks agents[, such as ...,] are configured")
  // is refused wherever it appears, appositive or not; the corrected text
  // scopes it to the configured agents ("Configured Agent Bricks agents").
  forbid(
    m,
    /(?<![Cc]onfigured )\bAgent Bricks agents(?:,[^.,;]{0,60},)? are (?:configured|set up)\b/,
    "custom Python agents are Agent Bricks too; only the configured ones are set up rather than coded",
  );
  const platform =
    /\bAgent Bricks\b[^.]*\bwhole agent platform, custom Python agents included\b/;
  assert.match(
    concept(m, "dbxfe-ai-platform-bricks-concept").definition,
    platform,
  );
  assert.match(
    pkgConcept(m, "dbxfe-ai-platform-l01-bricks-concept").definition,
    platform,
  );
  assert.match(section(m, "dbxfe-ai-platform-l01-map"), platform);
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-operations
// ---------------------------------------------------------------------------

test("operations: job failure notifications are not limited to FAILED, TIMED_OUT and internal errors", () => {
  // Source: databricks-sdk-py 9df82c7 service/jobs.py JobNotificationSettings
  // (no_alert_for_canceled_runs, no_alert_for_skipped_runs): canceled and
  // skipped runs notify unless muted.
  // The trigger is a sentence that states the notified SET (covers, only,
  // "Runs ending" as a scope cell); a sentence saying a notification fires
  // on FAILED or TIMED_OUT is true and is not the finding.
  const m = files.operations;
  requireQualifier(
    m,
    [
      /\bFAILED\b/,
      /\bTIMED_OUT\b/,
      /\b(?:only|just|solely|exclusively|limited to|restricted to|cover(?:s|ing)?|Runs ending)\b/i,
    ],
    /\bcanceled or skipped\b/i,
    "a sentence listing the notified end states includes canceled or skipped runs",
    SENTENCE,
  );
  forbid(
    m,
    /\b(?:only|just|solely|exclusively) (?:fire |fires |sent )?(?:for|on) FAILED\b|\bTIMED_OUT runs only\b|\b[Ss]ent only for\b/,
    "the notified set is wider",
  );
  const muted = /canceled or skipped runs unless muted/;
  assert.match(claim(m, "dbxfe-operations-claim-notify").description, muted);
  assert.match(
    pkgClaim(m, "dbxfe-operations-course-claim-runs").description,
    muted,
  );
  assert.match(
    byId(
      byId(visual(m, "dbxfe-operations-alerts-visual").states, "job").nodes,
      "fail",
    ).detail,
    muted,
  );
  assert.match(section(m, "dbxfe-operations-l01-ownership"), muted);
  beatMoved(m, "dbxfe-operations-alerts", "dbxfe-operations-scope");
  assert.equal(card(m, "dbxfe-operations-l01-card3").revision, "2");
  lessonMoved(m);
});

test("operations: VACUUM is not taught to remove every file older than 7 days", () => {
  // Source: delta-io/delta 6d055c5 docs/source/delta-utility.md: VACUUM
  // removes files no longer referenced by the table and older than the
  // retention threshold.
  const m = files.operations;
  forbid(
    m,
    /(?<!\b(?:not|never)\b[^.;:]{0,15})\bfiles? older than (?:the )?(?:7|seven)[- ]days?\b|(?<!\b(?:not|never|n't)\s)\b(?:removes?|deletes?|cleans? up|purges?)\b[^.;]{0,20}\bfiles? older than\b/i,
    "VACUUM removes only unreferenced files past retention",
  );
  assert.match(
    card(m, "dbxfe-operations-l01-card12").explanation,
    /no longer references/,
  );
  assert.match(
    section(m, "dbxfe-operations-l01-backup"),
    /no longer references/,
  );
  assert.match(
    optionOf(
      m.teaching.questions,
      "dbxfe-operations-backup-question",
      "dbxfe-operations-backup-question-b",
    ).rationale,
    /stopped referencing/,
  );
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-genai-eval
// ---------------------------------------------------------------------------

test("genai-eval: Safety and RetrievalRelevance are not taught as Databricks-only in MLflow 3.16.1", () => {
  // Sources: mlflow/mlflow 32792af mlflow/genai/scorers/builtin_scorers.py,
  // mlflow/genai/judges/builtin.py, judges/utils/__init__.py and
  // judges/constants.py: both run on a non-Databricks judge model; only the
  // model `databricks` calls the managed judge.
  const m = files["genai-eval"];
  forbid(
    m,
    /\b(?:Safety|RetrievalRelevance|judges?)\b[^.]{0,80}\bavailable only in Databricks\b|\bavailability differs between open-source and managed\b|\b(?:Safety|RetrievalRelevance)\b[^.]{0,60}\b(?:(?:is|are) (?:Databricks-only|Databricks-managed only)|only (?:work|works|run|runs) (?:in|on) Databricks)\b|\bonly (?:in )?Databricks(?:-managed)?(?: MLflow)?\b[^.;]{0,30}\b(?:Safety|RetrievalRelevance)\b/i,
    "the 3.16.1 package runs both judges outside Databricks (the review app's Databricks-only status is a different feature)",
  );
  forbid(
    m,
    /\blists `?(?:Safety|RetrievalRelevance)`?[^.]{0,40}\bas (?:Databricks-managed|available) only\b/i,
    "the page's note is attributed, not stated as fact",
  );
  assert.match(
    beat(m, "dbxfe-genai-eval-grounded").handbook.markdown,
    /also runs on a non-Databricks judge model/,
  );
  const mlflow = beat(m, "dbxfe-genai-eval-mlflow").handbook.markdown;
  assert.match(
    mlflow,
    /not an open-source versus Databricks difference in 3\.16\.1/,
  );
  assert.match(mlflow, /openai:\/gpt-4\.1-mini/);
  assert.match(
    claim(m, "dbxfe-genai-eval-claim-builtin").description,
    /also run on non-Databricks judge models/,
  );
  beatMoved(m, "dbxfe-genai-eval-grounded", "dbxfe-genai-eval-mlflow");
});

test("genai-eval: the retrieval judges are not said to look for chunk metadata", () => {
  // Source: mlflow/mlflow 32792af mlflow/genai/utils/trace_utils.py: the
  // 3.16.1 retrieval judges read each document's text and doc_uri and skip a
  // document that is not a dictionary.
  const m = files["genai-eval"];
  forbid(
    m,
    /\bretrieval judges\b[^.]{0,30}\blook for\b|\bjudges lose the chunk boundaries\b|\bretrieval judges\b[^.]{0,30}\b(?:need|needs|require|requires|expect|expects|use|uses)\b[^.]{0,30}\bchunk(?:_id| metadata| boundaries)\b/i,
    "the judges read text and doc_uri; chunk_id is what the UI may look for",
  );
  const retriever = extension(m, "dbxfe-genai-eval-extension-retriever");
  assert.match(
    retriever.explanation,
    /skip any retrieved document that is not a dictionary/,
  );
  assert.match(
    claim(m, "dbxfe-genai-eval-claim-span").description,
    /skip any document that is not a dictionary/,
  );
  assert.equal(retriever.revision, "2");
});

test("genai-eval: the MT-Bench study is not said to have reported measured judge biases", () => {
  // Sources: lm-sys/lm-sys.github.io 722a68b blog/2023-06-22-leaderboard.md
  // and lm-sys/FastChat 587d5cf fastchat/llm_judge/common.py: the authors
  // list position, verbosity and self-enhancement bias among potential
  // limitations.
  const m = files["genai-eval"];
  forbid(
    m,
    /\b(?:reported|found|showed|shown|measured|demonstrated|established|proved|proven|observed|identified|documented|confirmed)\b[^.]{0,20}\bposition(?: bias)?, verbosity(?: bias)?,? and self-enhancement\b/i,
    "the biases are listed as potential limitations",
  );
  const limitations = /among the (?:judges' )?potential limitations/;
  assert.match(beat(m, "dbxfe-genai-eval-judges").explanation, limitations);
  assert.match(
    claim(m, "dbxfe-genai-eval-claim-judging").description,
    limitations,
  );
  assert.match(
    pkgClaim(m, "dbxfe-genai-eval-course-claim-judging").description,
    limitations,
  );
  assert.match(section(m, "dbxfe-genai-eval-l01-judges"), limitations);
  beatMoved(m, "dbxfe-genai-eval-judges");
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-delta-writes
// ---------------------------------------------------------------------------

test("delta-writes: MERGE is not said to refuse every duplicate match", () => {
  // Source: delta-io/delta 6d055c5 commands/MergeIntoCommandBase.scala: the
  // refusal is for several source rows trying to modify one target row.
  // The flat RULE is the finding: an unconditional-DELETE-only MERGE and the
  // insert-only path are not refused. The clauses question's rationale about
  // the lab's UPDATE MERGE was judged already scoped and stays.
  const m = files["delta-writes"];
  forbid(
    m,
    /\bsource rows for one (?:matched )?target row\b[^.;]{0,40}\b(?:stops?|refuses?)\b|\bMERGE fails when several source rows match\b|\bMERGE (?:fails|errors|aborts)\b[^.;]{0,15}\bwhen(?:ever)? (?:several|two|multiple|more than one) source rows match\b|\b(?:refuses?|rejects?) (?:a|the|any) MERGE\b[^.;]{0,10}\b(?:when|whenever|if) (?:several|two|multiple|more than one) source rows match\b|\b(?:any|every) MERGE (?:with|that has|containing) duplicate(?:d)? source rows\b/i,
    "only rows updating one target row are refused",
  );
  assert.match(
    beat(m, "dbxfe-delta-writes-duplicate").title,
    /updating one target row/,
  );
  assert.match(
    pkgClaim(m, "dbxfe-delta-writes-course-claim-duplicate").description,
    /\bcan fail\b/,
  );
  beatMoved(m, "dbxfe-delta-writes-duplicate");
});

test("delta-writes: renames and drops do not always need column mapping", () => {
  // Source: delta-io/delta 6d055c5 docs/source/delta-batch.md: a table can
  // instead be rewritten with overwriteSchema.
  const m = files["delta-writes"];
  requireQualifier(
    m,
    [
      /\b(?:renam\w*|drops?|dropping)\b/i,
      /\b(?:need|needs|needed|require|requires|required)\b[^.;]{0,10}\bcolumn mapping\b|\bcolumn mapping\b[^.;]{0,10}\b(?:is |are )?(?:needed|required)\b/i,
    ],
    /\bwithout rewriting\b|\boverwriteSchema\b/i,
    "column mapping is needed only without rewriting data files",
    SENTENCE,
  );
  assert.match(
    beat(m, "dbxfe-delta-writes-evolution").handbook.markdown,
    /otherwise the table is rewritten with `overwriteSchema`/,
  );
  beatMoved(m, "dbxfe-delta-writes-evolution");
});

test("delta-writes: a protocol upgrade is not taught as irreversible without DROP FEATURE", () => {
  // Sources: delta-io/delta 6d055c5 docs/source/delta-drop-feature.md,
  // commands/alterDeltaTableCommands.scala and TableFeature.scala.
  const m = files["delta-writes"];
  forbid(
    m,
    /\bprotocol upgrades? (?:are|is) (?:irreversible|permanent|one-way)\b|\bprotocol upgrades? (?:cannot|can't|can never) be (?:undone|reversed|rolled back)\b|\bupgrading (?:a |the )?(?:table's )?protocol is (?:irreversible|permanent)\b|\bin later Delta releases\b/i,
    "DROP FEATURE exists from Delta 3.0.0",
  );
  // A clause saying the protocol cannot go back is the documentation's
  // wording, attributed, or is limited ("simply", some features).
  requireQualifier(
    m,
    [
      /\bprotocol\b/i,
      /\b(?:cannot|can't|can never|could never) be (?:downgraded|undone|reversed|rolled back)\b/i,
    ],
    /\bsays\b|\bdocumentation\b|\bpage\b|\bDROP FEATURE\b|\bsome features\b/i,
    "a protocol that cannot go back is attributed or limited to some features",
  );
  const handbook = beat(m, "dbxfe-delta-writes-features").handbook.markdown;
  assert.match(handbook, /from Delta 3\.0\.0/);
  assert.match(handbook, /DROP FEATURE/);
  assert.match(
    handbook,
    /changeDataFeed, clustering and domainMetadata, cannot be dropped in 4\.0\.0/,
  );
  assert.match(
    claim(m, "dbxfe-delta-writes-claim-features").description,
    /cannot simply be undone/,
  );
  assert.match(
    pkgClaim(m, "dbxfe-delta-writes-course-claim-features").description,
    /cannot simply be undone/,
  );
  beatMoved(m, "dbxfe-delta-writes-features");
});

test("delta-writes: changing Hive-style partitioning later does not need a new table", () => {
  // Source: delta-io/delta 6d055c5 docs/source/delta-batch.md (overwrite
  // with overwriteSchema rewrites the layout).
  const m = files["delta-writes"];
  forbid(
    m,
    /(?<!\bno )\bnew table (?:is )?(?:needed|required)\b|(?<!\bnot |n't |\bnever )\b(?:needs?|requires?|means?) a new table\b/i,
    "an overwriteSchema rewrite changes the partitioning",
  );
  const compare = byId(
    visual(m, "dbxfe-delta-writes-clustering-visual").states,
    "compare",
  ).table!;
  const later = compare.columns.indexOf("Change later");
  assert.ok(later >= 0, "the comparison has a Change later column");
  assert.match(compare.rows[0][later], /rewrite all data \(overwriteSchema\)/);
  beatMoved(m, "dbxfe-delta-writes-clustering");
});

// ---------------------------------------------------------------------------
// dbxfe-apps
// ---------------------------------------------------------------------------

test("apps: the SQL connector does not pick up the app's credentials without code", () => {
  // Sources: databricks/databricks-sql-python 70427d7
  // src/databricks/sql/auth/auth.py (no environment lookup) and
  // databricks-sdk-py 9df82c7 config.py (Config() reads the environment).
  const m = files.apps;
  forbid(
    m,
    /\bpick (?:them|it) up without code\b|\bconnectors?\b(?:(?!\bnot\b|\bnever\b|n't\b)[^.]){0,60}\b(?:without code|automatically|on (?:its|their) own)\b|\bSQL connector\b(?:(?!\bnot\b|\bnever\b|n't\b)[^.]){0,30}\breads?\b[^.]{0,40}\benvironment\b/i,
    "the SQL connector needs the SDK's credentials passed to it",
  );
  // query_as_app already passed credentials_provider before the correction;
  // what is new is the reason: the connector reads no environment.
  assert.match(
    beat(m, "dbxfe-apps-identity").handbook.markdown,
    /\bSQL connector does not\b[^.]*\bcredentials_provider\b/,
  );
  beatMoved(m, "dbxfe-apps-identity");
});

test("apps: a row filter is evaluated for the app's principal, not skipped", () => {
  // Sources: databricks/devhub 35f4745
  // src/content/docs/lakehouse/analytical-reads.md and databricks-sdk-py
  // 9df82c7 service/catalog.py: filters and masks are evaluated on every
  // access for whichever principal runs the query.
  const m = files.apps;
  forbid(
    m,
    /\bnever consulted\b|\bNot evaluated\b|\bdo(?:es)? nothing for the app's principal\b|\bmoves from excluded to applied\b|\bfilters?\b(?:(?!\b(?:not|never|cannot)\b)[^.;]){0,30}\b(?:skipped|bypassed|ignored)\b/i,
    "under app authorization the filter runs for the app's principal",
  );
  const appState = byId(
    visual(m, "dbxfe-apps-identity-visual").states,
    "app-identity",
  );
  const filter = byId(appState.nodes, "filter");
  assert.notEqual(filter.status, "excluded");
  assert.match(filter.detail, /Evaluated for the app's principal/);
  assert.ok(
    appState.connections.some(
      (c) => c.from === "filter" && /evaluated for the app/.test(c.label),
    ),
    "the app state draws the filter as evaluated for the app",
  );
  assert.match(
    beat(m, "dbxfe-apps-identity").handbook.markdown,
    /evaluated for the app's principal under app authorization/,
  );
  beatMoved(m, "dbxfe-apps-identity");
});

// ---------------------------------------------------------------------------
// dbxfe-bi
// ---------------------------------------------------------------------------

test("bi: a shared-permission publisher is not bounded by a single grant on one table", () => {
  // Sources: databricks-sdk-py 9df82c7 docs/workspace/dashboards/lakeview.rst
  // (publish with embed_credentials) and docs/workspace/catalog/tables.rst:
  // the publisher's DATA grants, over the objects the page reads, bound what
  // viewers reach.
  const m = files.bi;
  forbid(
    m,
    /\b(?:single|sole|only) (?:data )?grant\b|\bgranted only the accepted table\b|\bexposure to one table\b|\bone grant to maintain\b|\b(?:only|just|solely) (?:on )?the accepted table\b/i,
    "the bound is the principal's data grants over the accepted objects",
  );
  const objects = /data grants reach only the accepted objects/;
  assert.match(beat(m, "dbxfe-bi-credentials").handbook.markdown, objects);
  assert.match(section(m, "dbxfe-bi-l01-access"), objects);
  beatMoved(m, "dbxfe-bi-credentials");
  lessonMoved(m);
});

test("bi: a scheduled refresh does not always run on the dashboard's warehouse", () => {
  // Source: databricks-sdk-py 9df82c7 service/dashboards.py
  // (Schedule.warehouse_id).
  const m = files.bi;
  forbid(
    m,
    /\bqueries on the dashboard's warehouse,? so\b|(?<!\bnot )\b(?:always|only) (?:runs?|executes?|queries|uses?)\b[^.;]{0,30}\bdashboard's (?:own )?warehouse\b|(?<!\b(?:not|never)\b[^.;]{0,15})\b(?:runs?|executes?)\b(?:(?!\bnot\b)[^.;]){0,40}\bon the dashboard's (?:own )?warehouse\b(?!,? or on\b)/i,
    "a schedule can name its own warehouse",
  );
  assert.match(
    beat(m, "dbxfe-bi-refresh").handbook.markdown,
    /warehouse the schedule itself names/,
  );
  beatMoved(m, "dbxfe-bi-refresh");
});

// ---------------------------------------------------------------------------
// dbxfe-sharing
// ---------------------------------------------------------------------------

test("sharing: an alias is not offered for every shared object", () => {
  // Source: databricks-sdk-py 9df82c7 service/sharing.py (shared_as is for
  // table-like data objects).
  const m = files.sharing;
  forbid(
    m,
    /\b(?:each|every|any|all) (?:shared )?objects?(?: in (?:a|the) share)? can be (?:exposed under|given|shared under) (?:an )?alias(?:es)?\b/i,
    "shared_as applies to table-like objects",
  );
  assert.match(
    beat(m, "dbxfe-sharing-objects").handbook.markdown,
    /\btable-like shared object can be exposed under an alias\b/,
  );
  beatMoved(m, "dbxfe-sharing-objects");
});

test("sharing: UniForm's column mapping and protocol upgrade are not stated as irreversible facts", () => {
  // Sources: delta-io/delta 6d055c5 (v4.0.0) docs/source/delta-drop-feature.md
  // (column mapping droppable from Delta 3.3.0; no Iceberg compatibility
  // feature on the list) and commands/alterDeltaTableCommands.scala (a
  // feature another feature requires cannot be dropped).
  const m = files.sharing;
  forbid(m, /\birreversible protocol upgrades?\b/i, "DROP FEATURE exists");
  requireQualifier(
    m,
    [/\b(?:cannot|can't|can never|could never) be (?:turned off|undone)\b/i],
    /\bsays\b|\bpage\b/i,
    "'cannot be undone' is the UniForm page's wording and is attributed",
    SENTENCE,
  );
  requireQualifier(
    m,
    [
      /\b(?:column mapping|protocol|UniForm)\b/i,
      /\b(?:(?:cannot|can't|can never|could never) be (?:reversed|disabled|removed)|(?:is|are) (?:irreversible|permanent))\b/i,
    ],
    /\bsays\b|\bpage\b/i,
    "a UniForm step that cannot go back is the UniForm page's wording and is attributed",
    SENTENCE,
  );
  const handbook = beat(m, "dbxfe-sharing-uniform").handbook.markdown;
  assert.match(handbook, /DROP FEATURE/);
  assert.match(handbook, /from Delta 3\.3\.0/);
  assert.match(handbook, /Iceberg compatibility feature is not on its list/);
  assert.match(
    claim(m, "dbxfe-sharing-claim-uniform").description,
    /DROP FEATURE procedure lists column mapping as droppable from Delta 3\.3\.0/,
  );
  beatMoved(m, "dbxfe-sharing-uniform");
});

test("sharing: clean room outputs are not said to stay", () => {
  // Source: databricks-sdk-py 9df82c7 service/cleanrooms.py ("Expiration
  // time of the output schema of the task run (if any)"): only copies stay.
  const m = files.sharing;
  forbid(
    m,
    /(?<!copied )\boutputs (?:already written )?(?:stay|remain|persist)\b|\boutputs already written\b/i,
    "a run's output schema can expire; only copied outputs stay",
  );
  assert.match(
    beat(m, "dbxfe-sharing-cleanroom").handbook.markdown,
    /expiration time for a task run's output schema/,
  );
  assert.match(
    m.teaching.appliedTask.modelAnswer,
    /output schema can carry its own expiration time/,
  );
  beatMoved(m, "dbxfe-sharing-cleanroom", "dbxfe-sharing-decide");
});

// ---------------------------------------------------------------------------
// dbxfe-serving
// ---------------------------------------------------------------------------

test("serving: the query request shape is attributed to the SDK read, not an unread page", () => {
  // Sources: databricks-sdk-py 9df82c7 service/serving.py (query) and
  // mlflow/mlflow 32792af mlflow/pyfunc/scoring_server/__init__.py.
  const m = files.serving;
  forbid(
    m,
    /\bquery (?:page|documentation|docs)\b[^.]{0,30}\b(?:gives|shows|lists|describes|documents)\b|\baccording to the (?:Databricks )?query (?:page|documentation|docs)\b/i,
    "the query page's body was not fetched",
  );
  const sources = section(m, "dbxfe-serving-l01-sources");
  const unfetched = sources.split("page bodies were not fetched")[0];
  assert.notEqual(
    unfetched,
    sources,
    "the sources section names the unfetched pages",
  );
  assert.doesNotMatch(
    unfetched,
    /scoring server/,
    "the scoring server was read",
  );
  assert.match(sources, /MLflow's scoring server at its v3\.16\.1 tag/);
  const handbook = beat(m, "dbxfe-serving-contract").handbook.markdown;
  assert.match(
    handbook,
    /\bSDK for Python's API reference\b[^.]*\bquery call\b[^.]*\bfour input fields\b/,
  );
  assert.match(handbook, /`\/serving-endpoints\/\{name\}\/invocations`/);
  beatMoved(m, "dbxfe-serving-contract");
  lessonMoved(m, "1.1.0");
});

// ---------------------------------------------------------------------------
// dbxfe-retrieval
// ---------------------------------------------------------------------------

test("retrieval: the AI Search client's pre-rerank threshold is documented, not observed", () => {
  // Sources: databricks-sdk-py 9df82c7 service/aisearch.py (query_index) and
  // the databricks-ai-search 0.78 wheel's index.py.
  const m = files.retrieval;
  forbid(
    m,
    /\bAI Search client (?:applies|filters|drops|removes|discards|cuts)\b/i,
    "the client documents the order",
  );
  assert.match(
    card(m, "dbxfe-retrieval-l01-card11").explanation,
    /\bAI Search client documents\b[^.]*\bbefore reranking\b/,
  );
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// dbxfe-tools
// ---------------------------------------------------------------------------

test("tools: the MCP SDK does not check a token's audience unless audience validation is on", () => {
  // Sources: modelcontextprotocol/python-sdk 9972c21 (v2.2.0)
  // src/mcp/server/auth/settings.py (validate_token_resource defaults to None
  // and only warns), middleware/bearer_auth.py and provider.py.
  // The layers visual's door state shows a specification-conforming server
  // refusing a token issued for another server, and the decision kept it:
  // the finding is about what the SDK does by default.
  const m = files.tools;
  forbid(
    m,
    /\bexpired,? or wrong-audience\b|\b(?:checks|establishes) (?:a bearer token's )?audience, expiry\b|\bresource server URL is configured,? and refuses\b/i,
    "audience is checked only with validate_token_resource or by the verifier",
  );
  requireQualifier(
    m,
    [
      /\bSDK\b/,
      /\baudience\b|\banother server'?s?\b|\bwrong server\b|\b(?:issued|meant|intended) for (?:another|a different|the wrong)\b/i,
      /\b(?:refus|reject|check|establish|compar|verif|validat)\w*/i,
    ],
    /\bonly (?:when|once|if|with)\b|\benabled?\b|validate_token_resource|\bverifier\b|\bspecification requires\b|\bMUST\b/i,
    "a clause on the SDK's audience check carries its condition",
  );
  const handbook = beat(m, "dbxfe-tools-layers").handbook.markdown;
  assert.match(
    handbook,
    /`AuthSettings\.validate_token_resource` is set to `True`/,
  );
  assert.match(handbook, /warns and skips that comparison/);
  assert.match(
    claim(m, "dbxfe-tools-claim-mcp-auth").description,
    /only when AuthSettings\.validate_token_resource is enabled/,
  );
  assert.match(
    pkgClaim(m, "dbxfe-tools-course-claim-mcp-auth").description,
    /only when AuthSettings\.validate_token_resource is enabled/,
  );
  beatMoved(m, "dbxfe-tools-layers");
  lessonMoved(m);
});

test("tools: urllib3's method restriction is not applied to connection errors", () => {
  // Source: urllib3/urllib3 0248277 (2.6.3) src/urllib3/util/retry.py
  // (is_retry, _is_method_retryable): the allowed-methods check governs read
  // errors and retryable statuses; connect errors retry for any method.
  const m = files.tools;
  forbid(
    m,
    /\burllib3(?:'s `?Retry`?)? retries (?:by default only|GET\b)|\burllib3(?:'s `?Retry`?)? (?:only )?retries (?:by default )?(?:only\b|(?:GET|PUT|HEAD|DELETE|OPTIONS|TRACE)\b|idempotent\b)/i,
    "the idempotent-method default covers read errors and statuses only",
  );
  // Wherever a clause states urllib3's method restriction, it names the
  // errors the restriction governs (a read timeout, a reply, a status) or the
  // connection errors it does not.
  requireQualifier(
    m,
    [
      /\burllib3\b/i,
      /\bretr(?:y|ies|ied)\b/,
      /\b(?:GET|PUT|HEAD|DELETE|OPTIONS|TRACE|POST|idempotent)\b/,
    ],
    /\b(?:read|reply|replies|timed[- ]out|timeouts?|status(?:es)?|connect\w*)\b/i,
    "a clause stating the method restriction says which errors it governs",
  );
  assert.match(
    beat(m, "dbxfe-tools-timeout").handbook.markdown,
    /connection error, raised before the request is sent, is retried for any method/,
  );
  assert.match(
    claim(m, "dbxfe-tools-claim-retry").description,
    /connection errors, raised before the request is sent, are retried for any method/,
  );
  assert.match(
    pkgClaim(m, "dbxfe-tools-course-claim-retry").description,
    /read timeout/,
  );
  beatMoved(m, "dbxfe-tools-timeout");
  assert.equal(extension(m, "dbxfe-tools-extension-methods").revision, "2");
  lessonMoved(m);
});

// ---------------------------------------------------------------------------
// Across the fourteen modules
// ---------------------------------------------------------------------------

test("no corrected module calls the product a Genie space any more", () => {
  // Source: databricks/devhub 35f4745 src/content/docs/agents/genie.md: "A
  // Genie Agent (formerly Genie space)". The former name may be given as
  // such, and API identifiers such as genie_space keep their spelling.
  const hits = moduleNames.flatMap((name) =>
    files[name].allLeaves.flatMap((leaf) => {
      const hit = /(?<!formerly |former name, )\bGenie [Ss]paces?\b/.exec(
        leaf.text,
      );
      return hit
        ? [`dbxfe-${name} ${leaf.where}: …${excerpt(leaf.text, hit.index)}…`]
        : [];
    }),
  );
  assert.deepEqual(hits, []);
  // The beats that carried the old name as the product moved version.
  beatMoved(files["ai-platform"], "dbxfe-ai-platform-supervisor");
  beatMoved(files.apps, "dbxfe-apps-path");
  beatMoved(files.tools, "dbxfe-tools-layers");
});

// Every visual whose states the corrections changed, with the corrected
// phrase (from its finding) that must be drawn AND spoken.
const correctedVisuals: [ModuleName, string, RegExp][] = [
  ["aws", "dbxfe-aws-vpc-visual", /inbound only from the same group/],
  [
    "aws",
    "dbxfe-aws-responsibilities-visual",
    /instance profile set in the workspace's SQL warehouse configuration/,
  ],
  [
    "azure",
    "dbxfe-azure-identity-visual",
    /not provisioned; used through the storage credential/,
  ],
  [
    "azure",
    "dbxfe-azure-connector-visual",
    /Azure permission that authorizes reads/,
  ],
  ["azure", "dbxfe-azure-aws-visual", /A classic workspace: an Azure resource/],
  ["ai-platform", "dbxfe-ai-platform-map-visual", /deployed to \(legacy\)/],
  [
    "ai-platform",
    "dbxfe-ai-platform-supervisor-visual",
    /Work-order Genie Agent/,
  ],
  [
    "ai-platform",
    "dbxfe-ai-platform-custom-visual",
    /recommended path runs the agent in a Databricks App/,
  ],
  [
    "operations",
    "dbxfe-operations-alerts-visual",
    /canceled or skipped runs unless muted/,
  ],
  [
    "operations",
    "dbxfe-operations-scope-visual",
    /canceled or skipped unless muted/,
  ],
  [
    "delta-writes",
    "dbxfe-delta-writes-clustering-visual",
    /rewrite all data \(overwriteSchema\)/,
  ],
  ["apps", "dbxfe-apps-identity-visual", /Evaluated for the app's principal/],
  [
    "bi",
    "dbxfe-bi-credentials-visual",
    /data grants, reaching only the accepted objects/,
  ],
  ["sharing", "dbxfe-sharing-decide-visual", /copied outputs stay/],
];

function drawnText(v: TeachingVisual): string[] {
  return v.states.flatMap((s) => [
    s.title,
    s.explanation,
    ...s.nodes.flatMap((n) => [n.label, n.detail]),
    ...s.connections.map((c) => c.label),
    ...(s.table?.rows.flat() ?? []),
  ]);
}

test("every corrected visual still speaks its states: the text equivalent carries each title and node label", () => {
  for (const [name, id, corrected] of correctedVisuals) {
    const v = visual(files[name], id);
    for (const s of v.states) {
      assert.ok(
        v.textEquivalent.includes(s.title),
        `${id}: state title "${s.title}"`,
      );
      for (const n of s.nodes)
        assert.ok(
          v.textEquivalent.includes(n.label),
          `${id}/${s.id}: node label "${n.label}"`,
        );
    }
    assert.ok(
      drawnText(v).some((t) => corrected.test(t)),
      `${id}: a state draws the corrected ${corrected}`,
    );
    assert.match(
      v.textEquivalent,
      corrected,
      `${id}: the text equivalent says it too`,
    );
  }
});
