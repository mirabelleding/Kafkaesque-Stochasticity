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
    start="2026-11-23 10:00:00",
    end="2026-11-23 18:00:00",
)
```
*`start` is optional; if not specified, defaulting to the end of the fitted observation period.*

```python
forecasts.instantaneous_rates
forecasts.hourly_probabilities

forecasts.next_occurrence.cumulative_probabilities
forecasts.next_occurrence.probability_of_happenstance
forecasts.next_occurrence.subjects
forecasts.next_occurrence.ka_score_distribution
```

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

### 3. Probability of at Least One Occurrence

The primary prediction is:

```math
P\big(N_s(b)-N_s(a)\geq1\mid\mathcal H_a\big)
```

The calculation depends on the selected process, including whether its baseline incorporates calendar effects.

#### Model 1 — Poisson

For a homogeneous Poisson process with intensity $\lambda_0$ and interval length $h=b-a$:

```math
P\big(N(b)-N(a)\geq1\big)
=1-e^{-\lambda_0h}
```

For subject $s$ with a presence constraint, substitute its exposure time:

```math
p_s(a,b)=1-e^{-\lambda_{0,s}\tau_s(a,b)}
```

With `process="calendar_poisson"`, the intensity varies deterministically by day_of_week and hour. The probability becomes:

```math
p_s(a,b)=
1-\exp\left(
-\int_a^b P_s(t)\lambda_s(t)\,dt
\right)
```

The calendar-dependent formula also accommodates intervals of confirmed non-presence. With a constant intensity, it reduces to the homogeneous formula.

#### Model 2 — Hawkes

The probability of at least one occurrence uses the conditional intensity along the path where **no new event occurs** after forecast time $a$:

```math
\lambda^{(0)}(t\mid\mathcal H_a)
=
\mu(t)+
\sum_{t_i\lt a}\alpha e^{-\beta(t-t_i)},\qquad t\geq a
```

Here, $\mu(t)=\mu$ for `"hawkes"`; for `"calendar_hawkes"`, $\mu(t)$ follows the fitted calendar-dependent baseline.

For marked excitation, replace $\alpha$ with $\alpha(m_i)$ in the sum over **observed past occurrences**. Future marks affect the dynamics after future events, but the no-event path contains no such events.

For an individual subject model, including the presence constraint:

```math
p_s(a,b\mid\mathcal H_a)=
1-\exp\left(
-\int_a^b P_s(t)\lambda_s^{(0)}(t\mid\mathcal H_a)\,dt
\right)
```

Under a constant baseline, no presence interruptions, and a single-subject process, the integrated no-event intensity simplifies to:

```math
\int_a^b\lambda^{(0)}(t\mid\mathcal H_a)\,dt
=
\mu(b-a)
+
\frac{\alpha}{\beta}
\sum_{t_i\lt a}
\left(e^{-\beta(a-t_i)}-e^{-\beta(b-t_i)}\right)
```

If subjects excite one another, forecasting an event for a particular subject must also account for possible future events of other subjects. Simply treating their histories as frozen may not give the correct subject-specific interval probability.

#### Model 3 — Markov-Modulated Poisson Process

An MMPP accounts for uncertainty about the latent state and its transitions during the forecast interval.

For a time-homogeneous, two-state MMPP, let:

```math
\Lambda=\mathrm{diag}(\lambda_0,\lambda_1)
```

Let $\boldsymbol\pi_a$ be the column vector of filtered state probabilities at forecast time $a$, and let $\mathbf 1$ be a column vector of ones. Then, for $h=b-a$:

```math
p(a,b\mid\mathcal H_a)
=
1-\boldsymbol\pi_a^{\mathsf T}
\exp\big((Q-\Lambda)h\big)\mathbf 1
```

The matrix exponential accounts for state changes before the next event. With time-varying presence, replace $\Lambda$ with $P_s(t)\Lambda$ for a subject-specific model and propagate the state probabilities across the corresponding time intervals; a single constant matrix exponential is then insufficient.

### 4. Predicting the Subject of the Next Occurrence

Suppose each subject has a conditional intensity $\lambda_s(t)$. The combined instantaneous intensity is:

```math
\lambda_{\mathrm{total}}(t)=\sum_s\lambda_s(t)
```

Conditional on an event occurring at time $t$, its subject distribution is:

```math
P(S=s\mid\text{event at }t,\mathcal H_t)
=
\frac{\lambda_s(t)}{\sum_j\lambda_j(t)}
```

This instantaneous ratio is valid when the denominator is positive. It is **not** the probability that subject $s$ will have an event at any point during an entire day.

To predict the subject of the **first event in $[a,b]$**, a model with conditional no-event intensities $\lambda_s^{(0)}(t)$ can use:

```math
P(S_{\mathrm{next}}=s,\ T_{\mathrm{next}}\leq b\mid\mathcal H_a)
=
\int_a^b
\lambda_s^{(0)}(t)
\exp\left(
-\int_a^t\lambda_{\mathrm{total}}^{(0)}(u)\,du
\right)dt
```

A latent-state model such as an MMPP must additionally average over possible hidden-state trajectories. The first-event subject probabilities, together with the probability of **no occurrence**, sum to one.


### 5. Forecasting `ka_score`

The score forecast is a **probability distribution over possible marks**, conditional on an occurrence. For the first occurrence in a forecast interval $[a,b]$, define:

```math
p_m(a,b)
=
P(M_{\mathrm{next}}=m\mid T_{\mathrm{next}}\leq b,\mathcal H_a),
\qquad m\in\mathcal M
```

Where:

```math
\mathcal M=\{1,2,\ldots,10,\infty\}
```

The indefinite severity category is represented by:

```math
p_{\infty}(a,b)
=
P(M_{\mathrm{next}}=\infty\mid T_{\mathrm{next}}\leq b,\mathcal H_a)
```

The probabilities across all permitted categories sum to one:

```math
\sum_{m\in\mathcal M}p_m(a,b)=1
```

*The `"inf"` category represents severity beyond the finite scale, rather than a numerical magnitude. No single expected severity score is assumed.*

This conditions on at least one occurrence in the interval. A period with no occurrence has **no realized `ka_score`**; it is not assigned a score of zero.

The conditional expected score is:

```math
E[M_{\mathrm{next}}\mid T_{\mathrm{next}}\leq b,\mathcal H_a]
=
\sum_{m\in\mathcal M}m\,p_m(a,b)
```

The score forecast depends on both the possible event times and the applicable score distribution:

| Process | Forecasted `ka_score` |
|---|---|
| Poisson | Distribution of marks among expected events, optionally by subject; independent of past marks under the basic specification |
| Hawkes | Conditional mark distribution, potentially informed by event history; past marks may also affect event timing through $\alpha(m_i)$ |
| MMPP | Mixture of state-dependent mark distributions, accounting for hidden-state uncertainty and the states in which events are likely to occur |

When multiple occurrences are possible, the forecast refers to the **first occurrence** unless another target is defined explicitly. Score probabilities should be weighted by the likelihood of an event at each time; for an MMPP, simply averaging states without accounting for event intensity would generally be incorrect.

The subject and score may also be forecast jointly to investigate which subjects tend to be associated with which magnitudes of absurdity.

### 6. Hourly Forecasts and Probability Curves

**Hourly occurrence probabilities** describe the probability of at least one event in each hour. For history-dependent models, forecasts made for later hours must account for possible events and state changes in earlier forecast hours; simply freezing the current intensity is not generally sufficient.

**Conditional intensity curve:**

```math
t\longmapsto\lambda_s^*(t\mid\mathcal H_t)
```

This is an instantaneous event rate and may rise or fall over time.

**Cumulative probability curve:**

```math
F_s(t)=P(T_{\mathrm{next},s}\leq t\mid\mathcal H_a),
\quad \text{for }t\geq a
```

This is the probability that the next occurrence for subject $s$ happens by time $t$, starting from forecast time $a$. It can only increase or remain constant. Computing it under a multivariate history-dependent process or an MMPP requires accounting for other possible future events or latent-state transitions.

### 7. Subject-Specific and Environment-Wide Forecasts

The forecasting scope may be a single subject or the environment as a whole. Conditional `ka_score` forecasts follow the same scope.

For subject $s$, the model predicts whether that subject has at least one occurrence in the forecast interval:

```math
p_s(a,b)=P\left(N_s(b)-N_s(a)\geq1\mid\mathcal H_a\right)
```

For the environment, let $N_{\mathrm{total}}(t)=\sum_s N_s(t)$, assuming each occurrence is assigned to exactly one subject. Then:

```math
p_{\mathrm{total}}(a,b)=
P\big(N_{\mathrm{total}}(b)-N_{\mathrm{total}}(a)\geq1\mid\mathcal H_a\big)
```

At a given time, the environment-wide conditional intensity is the sum of the subject-specific intensities, including their presence constraints:

```math
\lambda_{\mathrm{total}}^*(t\mid\mathcal H_t)
=\sum_s P_s(t)\lambda_s(t\mid\mathcal H_t)
```

An environment-wide event means **at least one occurrence involving any subject**. Its probability must be calculated from the combined event process; it is not the sum of individual occurrence probabilities. For history-dependent and latent-state models, the calculation must account for their joint dynamics.

An environment-only model can forecast total occurrence probability without estimating subject-specific rates. Predicting which subject will be associated with the next event, however, requires a subject-aware model.

## Model Evaluation

The stochastic process models may be evaluated and compared using the following statistical metrics:

| Metric | Description |
|---|---|
| **Log-likelihood** | Measures how well a fitted model explains observed occurrences; higher values indicate better fit. |
| **Akaike Information Criterion (AIC)** | Balances goodness of fit against model complexity; lower values are preferred. |
| **Forecast log loss** | Evaluates predicted probabilities against observed outcomes; lower values indicate better predictive performance. |

Log-likelihood and AIC assess historical model fit, while forecast log loss evaluates out-of-sample predictive performance.

For additional evaluation methods, see [Methodology](docs/methodology.md#model-comparison-and-validation).