<!-- section:dbxfe-deep-learning-l01-outcome -->

After this lesson you can read shapes as contracts, compute a two-layer forward pass and its output gradient by hand, explain embeddings, separate training from inference memory, size a batch, choose fine-tuning or retrieval, explain data parallelism, and write a labelled accelerated design on the platform that a simpler baseline must fail first. Nothing here needs a GPU, a workspace or a download.

<!-- section:dbxfe-deep-learning-l01-start -->

Bring the baseline habit from [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01) and "a row times a column, summed". [Python for a SQL-fluent learner](#/lesson/dbxfe-python-bridge) is enough to read the NumPy example. Every number is synthetic and labelled, except the example's printed output, run on a CPU in this build.

<!-- section:dbxfe-deep-learning-l01-tensors -->

A tensor is an array of numbers with a shape: a tuple saying how many items each axis holds. NumPy keeps the item type, the dtype, separate; PyTorch's tensor is the same idea, float32 by default. For Cinderline's bearing monitor, one reading of two features is `(2,)`; a two-second vibration window is `(256, 3)`, 256 time steps by three axes; a batch of 32 windows is `(32, 256, 3)`. Read each axis as *what does this count*, batch first.

The shape is a contract. `(3, 2) @ (2, 2)` returns `(3, 2)` because the inner sizes agree; `(1, 3) @ (2, 2)` fails before any arithmetic, as run in this build:

```text
ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0,
with gufunc signature (n?,k),(k,m?)->(n?,m?) (size 2 is different from 3)
```

The message names both sizes. Inspect `.shape` and `.dtype` of both operands; the fix is usually a transpose, a reshape, or an upstream feature count.

<!-- section:dbxfe-deep-learning-l01-forward -->

A layer is a linear map followed by a bend. The map multiplies by a weight matrix and adds a bias; the bend, here ReLU, turns negatives into zero. Without it two layers collapse into one: W2(W1x + b1) + b2 = (W2W1)x + (W2b1 + b2). 3Blue1Brown's picture of units holding numbers is this arithmetic.

Hand-chosen, untrained weights; real code run on CPU in this build (Python 3.12.3, NumPy 2.5.3). **The reader app does not execute it.**

```python
import numpy as np

x  = np.array([0.5, 1.0])                  # one reading: shape (2,)
W1 = np.array([[1.0, -2.0], [0.5, 1.0]])   # layer 1 weights: (2, 2)
b1 = np.array([0.5, -1.0])
W2 = np.array([[2.0, 4.0]])                # layer 2 weights: (1, 2)
b2 = np.array([-0.5])

z1 = W1 @ x + b1                           # linear map
h  = np.maximum(z1, 0.0)                   # ReLU: negatives become 0
z2 = W2 @ h + b2
p  = 1 / (1 + np.exp(-z2))                 # sigmoid: score -> probability
loss = -np.log(p)                          # log loss for label y = 1
dW2  = (p - 1.0)[:, None] * h[None, :]     # gradient of loss w.r.t. W2

X = np.array([[0.5, 1.0], [2.0, 0.0], [-1.0, 0.5]])   # a batch: (3, 2)
P = 1 / (1 + np.exp(-(np.maximum(X @ W1.T + b1, 0.0) @ W2.T + b2)))

print("z1", z1, "h", h, "z2", z2, "p", p.round(4))
print("loss", loss.round(4), "dW2", dW2.round(4))
print("X", X.shape, "P", P.shape, P.round(4).ravel())
```

Output, as run:

```text
z1 [-1.    0.25] h [0.   0.25] z2 [0.5] p [0.6225]
loss [0.4741] dW2 [[-0.     -0.0944]]
X (3, 2) P (3, 1) [0.6225 0.989  0.3775]
```

For x = [0.5, 1.0]: unit one is 1.0×0.5 − 2.0×1.0 + 0.5 = −1.0, unit two 0.5×0.5 + 1.0×1.0 − 1.0 = 0.25. ReLU gives h = [0, 0.25]; the output is 4.0×0.25 − 0.5 = 0.5; the sigmoid gives 0.6225. The batch carries three readings through the same weights; the third switches both units off and lands on the bias, sigmoid(−0.5) = 0.3775.

<!-- section:dbxfe-deep-learning-l01-learning -->

A loss scores a prediction against its label. The reading was a real defect (y = 1), so the log loss is −ln(0.6225) = 0.4741; a perfect prediction scores 0. The gradient says how the loss changes as each weight changes. For a sigmoid with log loss the output gradient is p − y = −0.3775: the score should rise. One layer back, the gradient for W2 is (p − y) × h = [0, −0.0944]; the `-0.` is a signed zero, because unit one output nothing. With learning rate 0.1, W2[1] moves from 4.0 to about 4.0094 and p to 0.6230. Training repeats that step on batches; backpropagation is the chain rule, layer by layer.

A supplier code cannot be multiplied, so an embedding gives each id a row in a table, the vector the next layer multiplies. PyTorch documents `torch.nn.Embedding` as a lookup table of fixed dictionary and size; its rows move with the same gradients as every weight, so ids that predict alike drift together. Reserve an *unknown* row, or a new id has none. Retrieval indexes such as Databricks AI Search store vectors of this kind.

<!-- section:dbxfe-deep-learning-l01-resources -->

Training loops: forward pass on a batch, loss, backward pass, optimizer update, next batch, for many epochs. Inference is one forward pass with frozen weights: no labels, gradients or optimizer state. Databricks recommends the ML runtime with MLflow tracking and autologging for training runs.

A batch is the examples averaged into one update. With 64,000 windows, batch 16 gives 4,000 steps per epoch, batch 256 gives 250: fewer, smoother updates; retune the learning rate.

Training memory holds weights, gradients, optimizer state and a whole batch's activations; only the last grows with the batch. **Synthetic teaching example**: 5 million float32 parameters, two optimizer values per weight, an assumed 6 MB of activations per window.

| item | batch 32 | batch 128 | batch 512 |
|---|---|---|---|
| weights + gradients | 40 MB | 40 MB | 40 MB |
| optimizer state | 40 MB | 40 MB | 40 MB |
| activations | 192 MB | 768 MB | 3,072 MB |
| total vs 2,048 MB | 272 fits | 848 fits | 3,152 out of memory |

On *CUDA out of memory*, shrink the batch or accumulate gradients first; mixed precision (`torch.amp`) comes second because it changes numerics.

<!-- section:dbxfe-deep-learning-l01-scaling -->

"Make the model better" hides two requests. Fine-tuning continues training a model on your examples, so its weights change: format, tone, task pattern and vocabulary move. Retrieval leaves the weights alone and puts relevant passages into the input at inference, so what the model can cite changes when the index is rebuilt. Weekly bulletins fit retrieval: facts change and need citations. A fixed output format fits a prompt first, fine-tuning only after a measured gap. Databricks documents Foundation Model Fine-tuning as deprecated; its removal was scheduled for 14 August 2026, before this review, so check whether any part remains available. The documentation points to AI Runtime.

Data parallelism splits the work: every worker holds a full model copy and a different slice of the batch, an all-reduce averages their gradients, and every copy applies the same update. After an initial broadcast so every copy starts identical, only gradients travel each step. PyTorch's DistributedDataParallel synchronizes gradients during the backward pass; TorchDistributor launches such jobs as Spark jobs. The exchange costs about one gradient's bytes per step, so the documentation prefers one node with four GPUs to four one-GPU workers.

<!-- section:dbxfe-deep-learning-l01-platform -->

Three documented routes reach GPUs. **GPU-enabled compute**: the Machine learning checkbox, a GPU instance type as worker, optionally Single node, and Photon off, because Photon does not support GPU instance types. **AI Runtime**: serverless GPU with an A10 or H100 accelerator chosen for a notebook; single-node use was Public Preview and multi-GPU training Beta when read. **Distributors** in Databricks Runtime ML: TorchDistributor, DeepSpeed and Ray. A single-node GPU cluster is typically fastest and most cost-effective for development.

First ask whether a simpler model, or no model, meets the evidence. **Synthetic** held-out recall at 5% false alarms: an amplitude rule 55%, at no running cost; gradient-boosted trees on forty hand features 78%, on CPU; a two-dimensional CNN on the clips' (64, 126) spectrograms 83%, after unpriced GPU hours. The CNN earns its place only if the extra defects caught, priced per miss, exceed the GPU and upkeep cost.

<!-- section:dbxfe-deep-learning-l01-design -->

Designed before any GPU is requested: a weld clip becomes a `(64, 126)` spectrogram, a batch `(32, 1, 64, 126)`, the `(N, C, H, W)` input a 2-D CNN (`Conv2d`) takes; a 1-D CNN (`Conv1d`) would need `(32, 64, 126)`, the 64 frequency bins as channels.

| step | status | evidence |
|---|---|---|
| CPU smoke test, 512 clips | planned first | shapes, one loss, one step |
| single-node GPU, metrics logged per epoch | **NOT EXECUTED** | epoch time, recall |
| same node, several GPUs | **NOT EXECUTED**; if epoch time limits | epoch time vs one GPU |
| TorchDistributor across nodes | **NOT EXECUTED**; if a node is outgrown | step time vs one node |
| compare to trees | after the first GPU run | priced recall gain |

```python
# NOT EXECUTED in this build. Needs GPU-enabled compute (ML runtime,
# GPU instance type, Photon off) or AI Runtime (Public Preview; verify).
import time, torch, mlflow
model = Net().to("cuda")              # 2-D CNN (Conv2d) defined elsewhere
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
with mlflow.start_run():
    for epoch in range(epochs):
        start = time.time()
        for X, y in loader:           # X: (32, 1, 64, 126), y: (32,) integer labels
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                model(X.to("cuda")).squeeze(1), y.float().to("cuda"))  # the loss needs a float target
            opt.zero_grad(); loss.backward(); opt.step()
        mlflow.log_metric("epoch_seconds", time.time() - start, step=epoch)
        mlflow.log_metric("val_recall", val_recall(model), step=epoch)  # defined elsewhere
```

`mlflow.autolog()` is full only for PyTorch Lightning; for a plain loop like this it records just TensorBoard `SummaryWriter` scalars, with no notion of an epoch, so the loop logs the stop rule's evidence itself.

Stop if recall does not clear the priced threshold above the trees. Unknown: instance availability, AI Runtime status, quota, pricing, cost of a miss.

<!-- section:dbxfe-deep-learning-l01-exercise -->

1. With the worked weights, x = [2.0, 0.0] arrives. Compute z1, h, z2 and p.
2. At the synthetic rates (80 MB fixed, 6 MB per window), does batch 256 fit 2,048 MB? What do batch 64 and four accumulation steps need, and what effective batch results?
3. Two data-parallel workers split a batch of 256. What does each hold and exchange per step for 5 million float32 parameters?

<!-- section:dbxfe-deep-learning-l01-solution -->

1. z1 = h = [2.5, 0.0]; z2 = 4.5; p ≈ 0.989, the example's second batch row.
2. Batch 256: 80 + 256 × 6 = 1,616 MB, fits. Batch 64 accumulated four times: effective batch 256 but 80 + 64 × 6 = 464 MB, because activations exist for one small batch at a time. Synthetic.
3. Each holds a model copy, 128 windows' activations, gradients and optimizer state; they all-reduce gradients, about 5,000,000 × 4 bytes = 20 MB per worker per step.

<!-- section:dbxfe-deep-learning-l01-mistakes -->

- Trusting a shape-legal product: `X @ W1` runs on a `(3, 2)` batch but computes W1ᵀx per row.
- Sizing serving like training.
- Answering out-of-memory by adding workers.
- Fine-tuning facts that change weekly.
- Starting multi-node first.
- Planning on a preview or deprecated feature as if settled.
- Skipping the baseline.

<!-- section:dbxfe-deep-learning-l01-sources -->

3Blue1Brown (networks, gradient descent); NumPy ndarray; PyTorch tensor, Embedding, torch.amp, DDP; Databricks deep learning, best practices, GPU compute, AI Runtime, multi-GPU, distributed training, TorchDistributor, DeepSpeed, fine-tuning (deprecated), AI Search. Confirmed by search 2026-09-23; bodies not fetched.

<!-- section:dbxfe-deep-learning-l01-related -->

[Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01) is the habit applied here. [The MLflow module](#/module/dbxfe-mlflow) records runs, [the retrieval module](#/module/dbxfe-retrieval) completes fine-tune-or-retrieve, and [the FinOps module](#/module/dbxfe-finops) prices GPU hours.

<!-- section:dbxfe-deep-learning-l01-revisit -->

Return on an out-of-memory failure, a proposal to fine-tune away stale answers, a GPU request without a baseline, or when AI Runtime's status needs re-checking.
