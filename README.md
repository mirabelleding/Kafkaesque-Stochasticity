# A Study on Kafkaesque Stochasticity

This study examines the stochastic behaviour of Kafkaesque occurrences in workplace environments, exploring temporal patterns, event dependence, latent states, and probabilistic forecasting through competing stochastic process models.

> *І смішно, і грішно.*

## Database — Supabase

The project uses **Supabase PostgreSQL** for collecting and storing Kafkaesque occurrences. Supabase Auth provides contributor identification, while PostgreSQL provides relational storage and a function for authenticated record submissions.

### Database Schema

| Table | Description |
|---|---|
| `environments` | Environments in which occurrences are observed |
| `subjects` | Subjects associated with occurrences |
| `modalities` | Interaction modalities, such as meetings, calls, and messages |
| `occurrences` | Timestamped observations, Kafkaesque scores, and contributor references |
| `testimonies` | Descriptions associated with individual occurrences |
| `subject_presence` | Confirmed presence intervals for individual subjects |

The view `k_occurrences_v` consolidates occurrence records.

The PostgreSQL function `submit_occurrences()` validates authenticated submissions, resolves reference IDs, and atomically inserts occurrences and testimonies.

### Record Structure

```json
{
    "occurred_at": "2026-11-23 10:00:00",
    "environment": "Others",
    "modality": "Meeting",
    "subject": "annoyance_1",
    "ka_score": 9,
    "testimony": "..."
}
```

### Database Management

The database schema is maintained through versioned SQL migrations in `supabase/migrations/`, managed using the Supabase CLI.

Supabase is used for collecting real observations, while synthetic datasets can be generated directly in Python for model development and experimentation.



## Stochastic Process Models

#### Modelling Independence

The stochastic modelling library is **independent of Supabase and PostgreSQL**. It accepts observations as Python records or DataFrames, regardless of their original data source.

### Notation

Let:

- $N(t)$: Number of occurrences observed up to time $t$.
- $N_s(t)$: Number of occurrences associated with subject $s$ up to time $t$.
- $\lambda(t)$: Occurrence intensity (expected instantaneous event rate) at time $t$.
- $\mathcal{H}_t$: History of occurrences before time $t$.
- $t_i$: Timestamp of occurrence $i$.
- $m_i$: Mark associated with occurrence $i$, such as `ka_score`.
- $s$: Subject associated with an occurrence.

Intensity is a rate, not a probability. The following five processes are candidate descriptions of the event-arrival mechanism.

### Model 1 — Homogeneous Poisson Process

$$
\lambda(t)=\lambda_0
$$

The occurrence intensity is constant over time.

**Properties:**
- Constant event rate.
- Independent and stationary increments.
- Exponentially distributed interarrival times.

$$
\Delta T_i\sim\operatorname{Exponential}(\lambda_0)
$$

For an interval of duration $h$:

$$
N(t+h)-N(t)\sim\operatorname{Poisson}(\lambda_0h)
$$

### Model 2 — Calendar-Dependent Poisson Process

$$
\lambda(t)=
\exp\left(
\beta_0+
\beta_{\mathrm{weekday}(t)}+
\beta_{\mathrm{hour}(t)}
\right)
$$

A nonhomogeneous Poisson process (NHPP) whose deterministic intensity varies with calendar-related factors.

**Properties:**
- Time-varying baseline intensity.
- Different occurrence rates across weekdays and hours.
- Independent but generally nonstationary increments.

#### Model 3 — Hawkes Process

$$
\lambda(t\mid\mathcal H_t)
=
\mu+
\sum_{t_i<t}
\alpha e^{-\beta(t-t_i)}
$$

A self-exciting temporal point process in which previous occurrences temporarily increase future occurrence intensity.

**Parameters:**
- $\mu$: Baseline intensity.
- $\alpha$: Excitation amplitude.
- $\beta$: Exponential decay rate.

**Properties:**
- History-dependent intensity.
- Event clustering through self-excitation.
- The influence of previous occurrences decreases over time.
- For the stationary, univariate exponential-kernel model, $\alpha/\beta<1$ is the usual stability condition.

For a marked Hawkes process:

$$
\lambda(t\mid\mathcal H_t)
=
\mu+
\sum_{t_i<t}
\alpha(m_i)e^{-\beta(t-t_i)}
$$

Here, the excitation amplitude depends on the event's mark. The function $\alpha(m_i)$ must be specified and estimated; its relationship with `ka_score` should not be assumed in advance.

### Model 4 — Calendar-Dependent Hawkes Process

$$
\lambda(t\mid\mathcal H_t)
=
\mu(t)+
\sum_{t_i<t}
\alpha e^{-\beta(t-t_i)}
$$

Where the baseline intensity may be defined as:

$$
\mu(t)=
\exp\left(
\beta_0+
\beta_{\mathrm{weekday}(t)}+
\beta_{\mathrm{hour}(t)}
\right)
$$

Combines calendar-dependent baseline intensity with history-dependent excitation.

**Properties:**
- Weekday and hourly seasonality.
- Temporal dependence between occurrences.
- Potential event clustering beyond calendar-driven variations.

### Model 5 — Markov-Modulated Poisson Process (MMPP)

$$
\lambda(t\mid Z(t))=\lambda_{Z(t)}
$$

Where $Z(t)$ is a latent state governed by a continuous-time Markov chain.

For a two-state model:

$$
Z(t)\in\{0,1\}
$$

With state-dependent intensities:

$$
\lambda(t\mid Z(t))=
\begin{cases}
\lambda_0,&Z(t)=0\\
\lambda_1,&Z(t)=1
\end{cases}
$$

Where:
- $Z(t)=0$: Low-intensity state.
- $Z(t)=1$: High-intensity state.
- $\lambda_0$: Occurrence intensity in the low-intensity state.
- $\lambda_1$: Occurrence intensity in the high-intensity state.
- $\lambda_1>\lambda_0\geq0$.

The transition-rate matrix is:

$$
Q=
\begin{pmatrix}
-q_{01}&q_{01}\\
q_{10}&-q_{10}
\end{pmatrix}
$$

Where:
- $q_{01}$: Transition rate from state 0 to state 1.
- $q_{10}$: Transition rate from state 1 to state 0.

The expected duration of each state, assuming positive transition rates, is:

$$
E[D_0]=\frac{1}{q_{01}}
$$

$$
E[D_1]=\frac{1}{q_{10}}
$$

The probability of remaining in a state for at least duration $t$ is:

$$
P(D_0>t)=e^{-q_{01}t}
$$

$$
P(D_1>t)=e^{-q_{10}t}
$$

**Properties:**
- Event intensity depends on an underlying latent state.
- The latent state evolves according to a continuous-time Markov chain.
- The system may remain in the same state for an extended period.
- Conditional on the complete latent state trajectory, event arrivals follow a nonhomogeneous Poisson process.
- Observed occurrences can cluster during persistent high-intensity periods.
- Clustering does not require individual events to excite subsequent events.
- The model can infer probabilities of latent states from observed occurrence history.
- The number of latent states can be extended beyond two.

**Hypothesis:** Observed clustering may arise from persistent changes in the underlying environment rather than direct causal relationships between consecutive occurrences.


## Occurrence Forecasting

The objective is to predict the probability of one or more occurrences within a chosen interval, the subject associated with the next occurrence, and the evolution of those probabilities over time.

### 1. Observations and Forecast Intervals

An occurrence record contains at least:

- `occurred_at`: Event timestamp.
- `subject`: Subject associated with the event.

Optional fields include `ka_score`, `context`, and `project`. The model accepts records or DataFrames independently of where they were retrieved.

Let $[a,b]$ denote the forecast interval. The historical observation period must also be known: a day with **no recorded events** is informative only if events were being observed during that day. All timestamps and presence intervals must use a consistent time basis.

### 2. Subject Presence Constraint

Let $P_s(t)$ indicate whether subject $s$ is present:

$$
P_s(t)=
\begin{cases}
1,&\text{Subject is present}\\
0,&\text{Subject is non-present}
\end{cases}
$$

Apply the constraint to a subject-specific intensity:

$$
\lambda_s^*(t)=P_s(t)\lambda_s(t)
$$

Under an event definition requiring the subject's active participation:

$$
P_s(t)=0\implies\lambda_s^*(t)=0
$$

A minimal representation is `subject_id` and `presence_interval`, with each interval recording a period of confirmed presence. A Boolean at a single instant cannot describe a future or historical interval.

Missing presence information must not automatically be interpreted as non-presence. Using a hard zero requires the assumption that the subject cannot generate an event when non-present.

For a forecast interval, define the subject's total exposure time:

$$
\tau_s(a,b)=\int_a^b P_s(t)\,dt
$$

The presence constraint is common to all five candidate models. It changes the observable event intensity, but additional assumptions may be required about how a history-dependent or latent state evolves while the subject is non-present.

### 3. Estimating Model Parameters

The parameters must be learned from historical observations; the intensity equations alone do not provide fitted forecasts.

| Model | Parameters to estimate | General approach |
|---|---|---|
| Homogeneous Poisson | Constant intensity $\lambda_0$ | Event count divided by observed exposure |
| Calendar-dependent Poisson | Calendar coefficients $\beta$ | Poisson regression or point-process likelihood |
| Hawkes | Baseline $\mu$, excitation $\alpha$, decay $\beta$ | Event-time likelihood |
| Calendar-dependent Hawkes | Calendar coefficients and excitation parameters | Event-time likelihood with time-varying baseline |
| MMPP | State-specific intensities $\lambda_k$ and transition rates $q_{ij}$ | Latent-state likelihood / filtering |

For a homogeneous Poisson process observed over total exposure time $T$ with $n$ events:

$$
\hat{\lambda}_0=\frac{n}{T}
$$

Here, $T$ is **observed exposure**, not necessarily the elapsed number of calendar hours. A latent-state model requires a different estimation procedure because the underlying state is not directly observed.

### 4. Probability of at Least One Occurrence

The primary prediction is:

$$
P\big(N_s(b)-N_s(a)\geq1\mid\mathcal H_a\big)
$$

The calculation depends on the selected stochastic process.

#### Model 1 — Homogeneous Poisson

With constant rate $\lambda_0$ over an interval of length $h=b-a$:

$$
P\big(N(b)-N(a)\geq1\big)
=1-e^{-\lambda_0h}
$$

For subject $s$ with a presence constraint, substitute the observed exposure time:

$$
p_s(a,b)=1-e^{-\lambda_{0,s}\tau_s(a,b)}
$$

#### Model 2 — Calendar-Dependent Poisson

Integrate the deterministic, time-varying intensity over the forecast interval:

$$
p_s(a,b)=
1-\exp\left(
-\int_a^b P_s(t)\lambda_s(t)\,dt
\right)
$$

The integral accommodates different baseline rates by weekday or hour, as well as intervals of confirmed non-presence.

#### Model 3 — Hawkes

The probability of the **next** occurrence uses the intensity along the path where no new event occurs after forecast time $a$:

$$
\lambda^{(0)}(t\mid\mathcal H_a)
=
\mu+
\sum_{t_i<a}\alpha e^{-\beta(t-t_i)},\qquad t\geq a
$$

$$
p(a,b\mid\mathcal H_a)=
1-\exp\left(
-\int_a^b\lambda^{(0)}(t\mid\mathcal H_a)\,dt
\right)
$$

For a single-subject model, apply the presence indicator inside the integral. Under constant baseline and without presence interruptions, the integrated no-event intensity is:

$$
\int_a^b\lambda^{(0)}(t\mid\mathcal H_a)\,dt
=
\mu(b-a)
+
\frac{\alpha}{\beta}
\sum_{t_i<a}
\left(e^{-\beta(a-t_i)}-e^{-\beta(b-t_i)}\right)
$$

#### Model 4 — Calendar-Dependent Hawkes

The calculation is the same conditional survival calculation as Model 3, but with a time-varying baseline:

$$
\lambda^{(0)}(t\mid\mathcal H_a)
=
\mu(t)+
\sum_{t_i<a}\alpha e^{-\beta(t-t_i)}
$$

$$
p_s(a,b\mid\mathcal H_a)=
1-\exp\left(
-\int_a^b P_s(t)\lambda_s^{(0)}(t\mid\mathcal H_a)\,dt
\right)
$$

This expression gives a subject-specific next-event probability when modelling that subject's event process on its own. If subjects can excite one another, forecasting an event for one subject over a longer interval must also account for possible future events of the other subjects.

#### Model 5 — Markov-Modulated Poisson Process

An MMPP must account for uncertainty about the latent state and its possible transitions during the forecast interval.

For a time-homogeneous, two-state MMPP, let:

$$
\Lambda=
\operatorname{diag}(\lambda_0,\lambda_1)
$$

Let $\boldsymbol\pi_a$ be the column vector of filtered state probabilities at forecast time $a$, and let $\mathbf 1$ be a column vector of ones. Then, for $h=b-a$:

$$
p(a,b\mid\mathcal H_a)
=
1-\boldsymbol\pi_a^{\mathsf T}
\exp\big((Q-\Lambda)h\big)\mathbf 1
$$

The matrix exponential accounts for state changes before the next event. With time-varying presence, replace $\Lambda$ with $P_s(t)\Lambda$ and propagate the state probabilities across the corresponding time intervals; a single constant matrix exponential is no longer sufficient.

### 5. Predicting the Subject of the Next Occurrence

Suppose each subject has a conditional intensity $\lambda_s(t)$. The combined instantaneous intensity is:

$$
\lambda_{\mathrm{total}}(t)=\sum_s\lambda_s(t)
$$

Conditional on an event occurring at time $t$, its subject distribution is:

$$
P(S=s\mid\text{event at }t,\mathcal H_t)
=
\frac{\lambda_s(t)}{\sum_j\lambda_j(t)}
$$

This instantaneous ratio is valid when the denominator is positive. It is **not** the probability that subject $s$ will have an event at any point during an entire day.

To predict the subject of the **first event in $[a,b]$**, a model with conditional no-event intensities $\lambda_s^{(0)}(t)$ can use:

$$
P(S_{\mathrm{next}}=s,\ T_{\mathrm{next}}\leq b\mid\mathcal H_a)
=
\int_a^b
\lambda_s^{(0)}(t)
\exp\left(
-\int_a^t\lambda_{\mathrm{total}}^{(0)}(u)\,du
\right)dt
$$

A latent-state model such as an MMPP must additionally average over possible hidden-state trajectories. The first-event subject probabilities, together with the probability of **no occurrence**, sum to one.

### 6. Hourly Forecasts and Probability Curves

**Hourly occurrence probabilities** describe the probability of at least one event in each hour. For history-dependent models, forecasts made for later hours must account for possible events and state changes in earlier forecast hours; simply freezing the current intensity is not generally sufficient.

**Conditional intensity curve:**

$$
t\longmapsto\lambda_s^*(t\mid\mathcal H_t)
$$

This is an instantaneous event rate and may rise or fall over time.

**Cumulative probability curve:**

$$
F_s(t)=P(T_{\mathrm{next},s}\leq t\mid\mathcal H_a),\qquad t\geq a
$$

This is the probability that the next occurrence for subject $s$ happens by time $t$, starting from forecast time $a$. It can only increase or remain constant. Computing it under a multivariate history-dependent process or an MMPP requires accounting for other possible future events or latent-state transitions.

### 7. Subject-Specific and Environment-Wide Forecasts

The forecasting scope may be a single subject or the environment as a whole.

For subject $s$, the model predicts whether that subject has at least one occurrence in the forecast interval:

$$
p_s(a,b)=P\left(N_s(b)-N_s(a)\geq1\mid\mathcal H_a\right)
$$

For the environment, let $N_{\mathrm{total}}(t)=\sum_s N_s(t)$, assuming each occurrence is assigned to exactly one subject. Then:

$$
p_{\mathrm{total}}(a,b)=
P\big(N_{\mathrm{total}}(b)-N_{\mathrm{total}}(a)\geq1\mid\mathcal H_a\big)
$$

At a given time, the environment-wide conditional intensity is the sum of the subject-specific intensities, including their presence constraints:

$$
\lambda_{\mathrm{total}}^*(t\mid\mathcal H_t)
=\sum_s P_s(t)\lambda_s(t\mid\mathcal H_t)
$$

An environment-wide event means **at least one occurrence involving any subject**. Its probability must be calculated from the combined event process; it is not the sum of individual occurrence probabilities. For history-dependent and latent-state models, the calculation must account for their joint dynamics.

An environment-only model can forecast total occurrence probability without estimating subject-specific rates. Predicting which subject will be associated with the next event, however, requires a subject-aware model.


## Model Development

The model accepts occurrence records and optional subject-presence data as Python `mapping`, Pandas `DataFrame`, or Polars `DataFrame`.

### Initialization

```python
model = KafkaesqueModel(
    records=records,
    presence=presence,
    process="mmpp",
)

model.fit()
```

### Occurrence Forecasting

```python
forecast = model.predict(
    start="2026-11-23 09:00:00",
    end="2026-11-23 17:00:00",
)
```

Forecast results expose occurrence probabilities, expected counts, count distributions, hourly forecasts, subject probabilities, and temporal intensity curves through their attributes.

**Exempli gratia:**

```python
forecast.probability
forecast.hourly
forecast.subject
forecast.probability_curve
```

The optional `subject` argument restricts occurrence forecasts to a specified subject.