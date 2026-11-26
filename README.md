# Kafkaesque Stochasticity

This study examines the stochastic behaviour of Kafkaesque occurrences amidst the intricacies of existential absurdity, exploring temporal patterns, event dependence, latent states, and probabilistic forecasting through competing stochastic process models.

> *і смішно, і грішно.*

*For further [retrospections](https://github.com/mirabelleding/418teapot#pot_monologue).*

## Data Structures

### Kafkaesque Occurrences

```json
{
    "occurred_at": "2026-11-04 14:00:00",
    "environment": "Others",
    "modality": "Message",
    "subject": "annoyance_1",
    "ka_score": 9,
    "testimony": "'Tis some remarkable happenstance of absurdity."
}
```

| Attribute | Description |
|---|---|
| `occurred_at` | Timestamp of the occurrence |
| `environment` | Environmental context |
| `modality` | Interaction modality |
| `subject` | Subject associated with the occurrence |
| `ka_score` | **Kafkaesque Absurdity Score**: <br>An integer from `1` to `10`, its string representation (`"1"`–`"10"`), or `"inf"`. <br> *Higher finite scores indicate greater perceived absurdity without implying proportional differences in magnitude. <br> `"inf"` denotes severity beyond the finite scale and should be assigned sparingly, reserved for exceptional occurrences.* |
| `testimony` |  Description of the occurrence; *retained for descriptive and retrospective purposes, excluded from stochastic model estimation and forecasting.* |

#### Kafkaesque Absurdity Score - Scoring Guidelines

| Score | Severity | Description |
|---|---|---|
| 1–3 | Mild | Minor irrationality, logical inconsistency or bureaucratic inefficiency with limited practical consequences. |
| 4–6 | Moderate | Evidently unreasonable or counterproductive behaviour that obstructs productivity, rational decision-making or the stated objective. |
| 7–9 | Severe | Fundamental contradictions, substantial disregard for established facts, logical reasoning or practical constraints, with significant actual or potential consequences. |
| 10 | Extreme | Exceptional absurdity involving profound contradictions, an inversion of the stated objective or a fundamental disregard for rational, ethical or operational principles. |
| ∞ | Transcendent | Absurdity beyond the meaningful limits of the finite scoring framework, for which conventional severity comparisons become inadequate. |

### Subject Presence
`presence` is subject-specific and supports multiple intervals.

*When provided, it defines the complete exposure intervals, preventing absence from being misinterpreted as reduced occurrence intensity. All associated occurrences must fall within their subjects' presence intervals.*

```json
{
    "subject": "annoyance_1",
    "start": "2026-01-01 00:00:00",
    "end": "2026-07-01 23:59:59",
}
```
| Attribute | Description |
|---|---|
| `subject` | Subject identifier |
| `start` | Beginning of the presence interval |
| `end` | End of the presence interval (exclusive) |


### Data Storage

The project utilizes **Supabase PostgreSQL** for collection and storage of observations. For details, refer to the [Supabase Module](supabase/).

*The modelling library is **independent of Supabase and PostgreSQL**, accepting observations regardless of their original data source.*


## Kafkaesque Model

The model accepts occurrence records and optional subject-presence data as `mappings` or Pandas/Polars `DataFrame` objects.

### Instantiation and Model Fitting

```python
model = KafkaesqueModel(
    records=records,
    presence=presence,
    process="mmpp",
)

model.fit()
```
The `process` argument accepts `"poisson"`, `"calendar_poisson"`, `"hawkes"`, `"calendar_hawkes"`, or `"mmpp"`.

*`presence` is optional.*

### Forecasting

```python
forecasts = model.predict(
    start="2026-11-24 10:00:00",
    end="2026-11-24 18:00:00",
)
```
*`start` is optional; if not specified, defaulting to the end of the fitted observation period.*

#### Outputs

```python
forecasts.hourly_pmf
forecasts.cdf
forecasts.mark_distribution
forecasts.intensity
```

| Attribute | Dimensions | Description |
|---|---|---|
| `hourly_probability_mass` | `hour × count` | Probability mass function of occurrence counts within each forecast hour. |
|`cumulative_probability`|`time`|Cumulative density function of the next occurrence time.|
| `mark_distribution` | `occurrence × subject × ka_score` | Joint subject and Kafkaesque Absurdity Score probability distribution for each occurrence position within the forecast period. |
| `intensity` | `time` | Historical fitted intensity and forecasted expected instaneous rates.|


## Stochastic Process Models

### Notation

Let:

- $N(t)$: Number of occurrences observed up to time $t$.
- $N_s(t)$: Number of occurrences associated with subject $s$ up to time $t$.
- $\lambda(t)$: Occurrence intensity (expected instantaneous event rate) at time $t$.
- $\mathcal{H}_t$: History of occurrences before time $t$.
- $t_i$: Timestamp of occurrence $i$.
- $M_i$: `ka_score` associated with occurrence $i$, treated as a discrete random mark; $m_i$ is its observed value.
- $\mathcal M$: Set of permitted `ka_score` values.
- $s$: Subject associated with an occurrence.

*Intensity is a rate, not a probability.*

### Marked Occurrences

Each observation consists of an occurrence timestamp, a subject, and a `ka_score`. The marked conditional intensity can be expressed as:

```math
\lambda_s(t,m\mid\mathcal H_t)
=
\lambda_s(t\mid\mathcal H_t)
 f_s(m\mid t,\mathcal H_t)
```

Here, $f_s(m\mid t,\mathcal H_t)$ is the probability of score $m$ **given that an occurrence associated with subject $s$ happens at time $t$**. The probabilities across permitted scores sum to one:

```math
\sum_{m\in\mathcal M}f_s(m\mid t,\mathcal H_t)=1
```

This separates two forecasting objectives: **occurrence timing** and **occurrence magnitude, measured by `ka_score`**.
The three process families differ in how event history, calendar effects, and latent states enter these calculations.

### Model 1 — Poisson Process

With `process="poisson"`, the process is homogeneous, with constant intensity:

```math
\lambda(t)=\lambda_0
```

**Properties:**
- Constant event rate.
- Independent and stationary increments.
- Exponentially distributed interarrival times.

```math
\Delta T_i\sim\mathrm{Exponential}(\lambda_0)
```

For an interval of duration $h$:

```math
N(t+h)-N(t)\sim\mathrm{Poisson}(\lambda_0h)
```

With `process="calendar_poisson"`, the process becomes a nonhomogeneous Poisson process (NHPP). Its deterministic intensity incorporates day_of_week and hour effects:

```math
\lambda(t)=
\exp\left(
\beta_0+
\beta_{\mathrm{day\_of\_week}(t)}+
\beta_{\mathrm{hour}(t)}
\right)
```

Calendar dependence allows occurrence rates to differ across days of week and hours. Increments remain independent but are generally nonstationary.

**Marks:** The standard marked Poisson model also estimates a distribution of `ka_score`, such as $f_s(m)$ for each subject. Under independent marking, previous scores do not affect future event intensity. Calendar differences in the score distribution can be examined separately; selecting `"calendar_poisson"` specifies calendar effects in event intensity, not automatically in the `ka_score` distribution.

### Model 2 — Hawkes Process

With `process="hawkes"`, a self-exciting Hawkes process has constant baseline intensity:

```math
\lambda(t\mid\mathcal H_t)
=
\mu+
\sum_{t_i\lt t}
\alpha e^{-\beta(t-t_i)}
```

**Parameters:**
- $\mu$: Baseline intensity.
- $\alpha$: Excitation amplitude.
- $\beta$: Exponential decay rate.

**Properties:**
- History-dependent intensity.
- Event clustering through self-excitation.
- The influence of previous occurrences decreases over time.
- For the stationary, univariate exponential-kernel model, $\alpha/\beta\lt 1$ is the usual stability condition.

With `process="calendar_hawkes"`, the baseline becomes time-dependent while the excitation mechanism remains unchanged:

```math
\lambda(t\mid\mathcal H_t)
=
\mu(t)+
\sum_{t_i\lt t}
\alpha e^{-\beta(t-t_i)}
```

For example, the calendar-dependent baseline can be specified as:

```math
\mu(t)=
\exp\left(
\beta_0+
\beta_{\mathrm{day\_of\_week}(t)}+
\beta_{\mathrm{hour}(t)}
\right)
```

This allows comparisons between clustering explained by calendar effects and additional clustering associated with event history.

For a marked Hawkes process, the excitation amplitude may depend on an event's mark:

```math
\lambda(t\mid\mathcal H_t)
=
\mu(t)+
\sum_{t_i\lt t}
\alpha(m_i)e^{-\beta(t-t_i)}
```

The function $\alpha(m_i)$ allows an occurrence's `ka_score` to modify its subsequent excitation. The direction and magnitude of this relationship are estimated from historical data, rather than assuming that higher scores necessarily produce more events. An unmarked Hawkes model is the special case $\alpha(m_i)=\alpha$.

A conditional score distribution $f_s(m\mid t,\mathcal H_t)$ is also needed to forecast the `ka_score` of future occurrences. **Mark-dependent excitation** and **forecasting future marks** are distinct, although they can be fitted together. A marked specification additionally requires appropriate stability conditions.

### Model 3 — Markov-Modulated Poisson Process (MMPP)

```math
\lambda(t\mid Z(t))=\lambda_{Z(t)}
```

Where $Z(t)$ is a latent state governed by a continuous-time Markov chain.

For a two-state model:

```math
Z(t)\in\{0,1\}
```

With state-dependent intensities:

```math
\lambda(t\mid Z(t))=
\begin{cases}
\lambda_0,&Z(t)=0\\
\lambda_1,&Z(t)=1
\end{cases}
```

Where:
- $Z(t)=0$: Low-intensity state.
- $Z(t)=1$: High-intensity state.
- $\lambda_0$: Occurrence intensity in the low-intensity state.
- $\lambda_1$: Occurrence intensity in the high-intensity state.
- $\lambda_1\gt\lambda_0\geq0$.

The transition-rate matrix is:

```math
Q=
\begin{pmatrix}
-q_{01}&q_{01}\\
q_{10}&-q_{10}
\end{pmatrix}
```

Where:
- $q_{01}$: Transition rate from state 0 to state 1.
- $q_{10}$: Transition rate from state 1 to state 0.

The expected duration of each state, assuming positive transition rates, is:

```math
E[D_0]=\frac{1}{q_{01}}
```

```math
E[D_1]=\frac{1}{q_{10}}
```

The probability of remaining in a state for at least duration $t$ is:

```math
P(D_0\gt t)=e^{-q_{01}t}
```

```math
P(D_1\gt t)=e^{-q_{10}t}
```

**Properties:**
- Event intensity depends on an underlying latent state.
- The latent state evolves according to a continuous-time Markov chain.
- The system may remain in the same state for an extended period.
- Conditional on the complete latent state trajectory, event arrivals follow a nonhomogeneous Poisson process.
- Observed occurrences can cluster during persistent high-intensity periods.
- Clustering does not require individual events to excite subsequent events.
- The model can infer probabilities of latent states from observed occurrence history.
- The number of latent states can be extended beyond two.

**Hypothesis:** Observed clustering may arise from persistent shifts in latent intensity states rather than direct self-excitation between occurrences.

```math
P(M_i=m\mid Z(t_i)=k)=f_k(m)
```

Observed `ka_score` values inform latent-state inference, while future scores are forecast using state-dependent distributions.

The `"mmpp"` specification models intensity through latent states without explicit day of week or hour effects in its initial formulation.


## Probabilistic Forecasting

The objective is to forecast **occurrences timing, subjects involved, and the `ka_score` magnitude**, together with the evolution of occurrence probabilities and intensities over time.

### 1. Observations and Forecast Intervals

Let $[a,b]$ denote the forecast interval. Historical observations are assumed complete within the observation period; **intervals without recorded occurrences are treated as having zero occurrences.**

All timestamps and presence intervals must use a consistent time basis.

### 2. Subject Presence Constraint

Let $P_s(t)$ indicate whether subject $s$ is present:

```math
P_s(t)=
\begin{cases}
1,&\text{Subject is present}\\
0,&\text{Subject is non-present}
\end{cases}
```

Apply the constraint to a subject-specific intensity:

```math
\lambda_s^*(t)=P_s(t)\lambda_s(t)
```

Under an event definition requiring the subject's active participation:

```math
P_s(t)=0\implies\lambda_s^*(t)=0
```

A minimal representation is `subject` and `presence_interval`, with each interval recording a period of confirmed presence. A Boolean at a single instant cannot describe a future or historical interval.

When `presence=None`, no presence constraints are applied. Otherwise, occurrence intensity is restricted to the supplied presence intervals for the corresponding subjects.

For a forecast interval, define the subject's total exposure time:

```math
\tau_s(a,b)=\int_a^b P_s(t)\,dt
```

The presence constraint applies across all three process families. It changes the observable event intensity, but additional assumptions may be required about how a history-dependent or latent state evolves while the subject is non-present.

### 3. Hourly Occurrence Count Distribution

Let $N(t)$ denote the number of occurrences observed up to time $t$, and let $\mathcal H_a$ represent the historical information available at forecast time $a$.

The **probability mass function (PMF)** of the number of occurrences during an hour beginning at $t$ is:

```math
p_t(n)=P(N(t+1\mathrm{h})-N(t)=n\mid\mathcal H_a)
```

where $n\in\{0,1,2,\ldots\}$.

Each hourly timestamp identifies the beginning of a half-open interval. For example, `2026-11-24 10:00:00` represents 10:00 AM to 11:00 AM.

The probabilities across all possible counts sum to one:

```math
\sum_{n=0}^{\infty}p_t(n)=1
```

Several quantities can be derived from the PMF.

**Probability of at least one occurrence:**

```math
P(N_t\geq1)=1-p_t(0)
```

**Expected occurrence count:**

```math
E[N_t]=\sum_{n=0}^{\infty}n\,p_t(n)
```

**Cumulative count probability:**

```math
P(N_t\leq n)=\sum_{k=0}^{n}p_t(k)
```

For a homogeneous Poisson process with intensity $\lambda$, the hourly count distribution is:

```math
p_t(n)=\frac{\lambda^n e^{-\lambda}}{n!}
```

when $\lambda$ is expressed in occurrences per hour.

Calendar Poisson, Hawkes, and MMPP models calculate the same forecast quantity using their respective intensity dynamics.

For history-dependent or latent-state processes, hourly counts may be statistically dependent. Each hourly PMF is therefore calculated conditional on the observed history at the forecast origin, accounting for uncertainty about future occurrences and latent-state transitions.

### 4. Individual Occurrence Distributions

For the forecast period $[a,b)$, let $S_k$ and $M_k$ denote the subject and Kafkaesque Absurdity Score associated with the $k$-th occurrence in chronological order.

The joint probability distribution is:

```math
q_k(s,m)=P(S_k=s,M_k=m\mid N(b)-N(a)\geq k,\mathcal H_a)
```

where $s$ denotes a subject and $m\in\mathcal M$, with:

```math
\mathcal M=\{1,2,\ldots,10,\infty\}
```

Each occurrence distribution is conditional on that occurrence existing within the forecast period:

```math
\sum_s\sum_{m\in\mathcal M}q_k(s,m)=1
```

The marginal distributions are obtained by summation.

**Subject distribution:**

```math
P(S_k=s\mid N(b)-N(a)\geq k,\mathcal H_a)
=\sum_m q_k(s,m)
```

**KA score distribution:**

```math
P(M_k=m\mid N(b)-N(a)\geq k,\mathcal H_a)
=\sum_s q_k(s,m)
```

The `"inf"` category represents severity beyond the finite ordinal scale, not a numerical infinity.

These distributions describe individual occurrence positions without assuming that the corresponding occurrences will necessarily happen. They preserve subject–severity associations but do not constitute the full joint distribution of an entire future occurrence sequence.

### 5. Historical and Forecasted Intensity

The instantaneous occurrence intensity describes the rate at which events arise over time. For a stochastic point process, the conditional intensity is defined as:

```math
\lambda(t\mid\mathcal H_t)
=
\lim_{\Delta t\to0^+}
\frac{
P(N(t+\Delta t)-N(t)\geq1\mid\mathcal H_t)
}{
\Delta t
}
```

where $\mathcal H_t$ denotes the observed event history available immediately before time $t$.

*Intensity is an instantaneous rate, not a probability.* It is expressed in units such as occurrences per hour.

**Historical Intensity**

For historical timestamps, the fitted conditional intensity incorporates the observed occurrence history:

```math
\lambda_{\mathrm{historical}}(t)
=
\hat{\lambda}(t\mid\mathcal H_t)
```

where $\hat{\lambda}$ denotes the intensity evaluated using the estimated model parameters.

Its temporal behaviour depends on the selected stochastic process:

- **Poisson:** Constant intensity.
- **Calendar Poisson:** Intensity varies according to calendar effects.
- **Hawkes:** Observed occurrences increase intensity through self-excitation, followed by decay.
- **Calendar Hawkes:** Combines calendar-dependent baseline intensity with self-excitation.
- **MMPP:** Conditional intensity reflects the inferred probabilities of latent intensity states.

**Forecasted Intensity**

For future timestamps $t\geq a$, the occurrence history beyond the forecast origin $a$ is unknown. The forecasted intensity therefore represents the conditional expectation over possible future event histories:

```math
\bar{\lambda}(t\mid\mathcal H_a)
=
E\left[
\lambda(t\mid\mathcal H_t)
\mid\mathcal H_a
\right]
```

For history-dependent and latent-state models, this expectation accounts for uncertainty about future occurrences and latent-state transitions.

Historical fitted intensity and forecasted expected intensity are represented along a unified time axis, distinguished by their historical or forecast status.

**Relationship to Occurrence Count Probability**

The expected number of occurrences within a forecast interval $[a,b)$ is obtained by integrating the forecasted intensity:

```math
E[N(b)-N(a)\mid\mathcal H_a]
=
\int_a^b
\bar{\lambda}(t\mid\mathcal H_a)\,dt
```

The same expected count can be obtained from the corresponding count probability mass function:

```math
E[N(b)-N(a)\mid\mathcal H_a]
=
\sum_{n=0}^{\infty}n\,P(N(b)-N(a)=n\mid\mathcal H_a)
```

Thus, the intensity curve describes the temporal evolution of the occurrence rate, while the probability mass function describes the distribution of occurrence counts over an interval.

The two representations are complementary: hourly count distributions do not generally recover variations in instantaneous intensity within an hour.


## Model Evaluation

The stochastic process models may be evaluated and compared using the following statistical metrics:

| Metric | Description |
|---|---|
| **Log-likelihood** | Measures how well a fitted model explains observed occurrences; higher values indicate better fit. |
| **Akaike Information Criterion (AIC)** | Balances goodness of fit against model complexity; lower values are preferred. |
| **Forecast log loss** | Evaluates predicted probabilities against observed outcomes; lower values indicate better predictive performance. |

Log-likelihood and AIC assess historical model fit, while forecast log loss evaluates out-of-sample predictive performance.

For additional evaluation methods, see [Methodology](docs/methodology.md#model-comparison-and-validation).