# Statistical Analysis Methodology

The analysis examines calendar dependence, event history, and `ka_score` through parameter estimation, statistical inference, and out-of-sample validation.

## Parameter Estimation

Model parameters are estimated from historical occurrence timestamps, subjects, and marks.

| `process` | Temporal parameters | `ka_score` parameters | Estimation method |
|---|---|---|---|
| `"poisson"` | Constant intensity $\lambda_0$ | Score distribution, potentially by subject | Exposure-based estimation |
| `"calendar_poisson"` | Day-of-week and hourly coefficients $\beta$ | Conditional score distribution | Poisson regression or point-process likelihood |
| `"hawkes"` | Baseline $\mu$, excitation $\alpha$, decay $\beta$ | Score distribution and mark-dependent excitation $\alpha(m)$ | Marked point-process likelihood |
| `"calendar_hawkes"` | Calendar baseline, excitation, and decay | Score distribution and mark-dependent excitation $\alpha(m)$ | Marked point-process likelihood with calendar baseline |
| `"mmpp"` | State intensities $\lambda_k$, transition rates $q_{ij}$ | State-conditional score distributions $f_k(m)$ | Latent-state likelihood and filtering |

For a homogeneous Poisson process with $n$ occurrences over observed exposure $T$:

```math
\hat{\lambda}_0=\frac{n}{T}
```

Exposure accounts for observation periods and applicable subject-presence constraints.

For a marked point process, the conditional log-likelihood incorporates event timing and marks:

```math
\ell
=
\sum_i\log\lambda(t_i\mid\mathcal H_{t_i})
-
\int_0^T\lambda(t\mid\mathcal H_t)\,dt
+
\sum_i\log f(m_i\mid t_i,\mathcal H_{t_i})
```

Subject-specific and latent-state models require their corresponding likelihood formulations. The ordinal nature of `ka_score` must be respected.

## Calendar Dependence

Calendar effects are assessed by comparing `"poisson"` with `"calendar_poisson"`, and `"hawkes"` with `"calendar_hawkes"`.

| Analysis | Objective |
|---|---|
| Day-of-week and hourly occurrence rates | Identify variation in observed event frequency |
| Calendar coefficients | Estimate temporal effects on occurrence intensity |
| Likelihood-ratio test | Assess additional calendar terms under appropriate nesting assumptions |
| AIC / BIC | Compare model fit relative to complexity |
| Out-of-sample forecasting | Evaluate predictive improvement from calendar effects |

Comparisons must account for unequal observation exposure. Calendar effects on **occurrence intensity** and **`ka_score` distributions** are investigated separately; selecting a calendar-dependent process does not establish either relationship.

## Mark Dependence and Severity

The attribute `ka_score` is examined as both a predictor of subsequent occurrences and a forecast target.

| Analysis | Objective |
|---|---|
| Score distributions by subject and calendar period | Identify variation in event severity |
| `ka_score` and subsequent interarrival times | Examine associations between severity and event timing |
| Marked versus unmarked Hawkes | Assess the predictive contribution of mark-dependent excitation |
| State-dependent scores in MMPP | Examine relationships between severity and latent intensity states |
| Out-of-sample score forecasts | Evaluate predicted score distributions and expected scores |

*Relationships between `ka_score`, excitation, and latent states are estimated rather than imposed. Statistical association does not establish causation.*

## Model Comparison and Validation

Models are evaluated using chronological training and validation periods to prevent future-information leakage.

- **Occurrence prediction:** Log loss, Brier score, and event-time likelihood where applicable.
- **Severity prediction:** Conditional score-distribution log loss, supplemented by expected-score error.
- **Model selection:** Likelihood-based comparisons, AIC/BIC, and out-of-sample predictive performance.

Statistical significance, goodness of fit, and predictive performance are evaluated separately. Sparse observations may limit reliable estimation of calendar effects, mark dependence, and latent-state dynamics.