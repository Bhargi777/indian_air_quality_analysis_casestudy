# Four-Person Notebook Evaluation Plan

This split assigns connected material to each presenter while balancing the workload across data preparation, exploratory analysis, statistical evidence, and modelling. Each person should explain the question, the method, the notebook evidence/visual, and the takeaway. The BI build guide is not a speaking topic; the visualization deliverable is noted separately below. The notebook remains the source of truth; this file is only the speaking-plan map.

## Presenter 1 - Dataset, preprocessing, and data trust

**Notebook material:** Part A (A1-A11), the start of Part B (B1-B4), Q1-Q3, Q13, and the preprocessing/EDA conclusion.

**Explain:** What the city-day and station-day datasets contain; date keys and granularity; duplicates, missingness, invalid or implausible values, outliers, skew, transformations, engineered fields, station merge, and saved clean files. Then describe coverage imbalance and why median AQI, spread, and spikes matter in addition to a mean. Use Q13 to explain which unusual values could affect the story, including the Ahmedabad CO/AQI anomaly, and how it was handled or caveated.

**Core takeaway:** Cleaning choices and unequal coverage affect what conclusions the later analyses can support. Preserve the caveat: cleaning does not make the data complete or remove every limitation.

## Presenter 2 - Pollutants, seasonality, and geographic patterns

**Notebook material:** Remaining EDA (B5-B9), Q4-Q8, Q14, and the descriptive comparisons that support those questions.

**Explain:** City and region differences; time trends; station/state views; how pollutant measurements relate to AQI and to one another; fine-particle share; seasonal patterns; and whether year-to-year trends persist when city composition is considered. Point to each question's chart/table and say what the visual supports and what it cannot establish.

**Core takeaway:** Air quality varies by place, time, and pollutant. Distinguish descriptive patterns from explanations or causal claims.

## Presenter 3 - Events, reliability, and hypothesis tests

**Notebook material:** Q9-Q11; Part 3 statistical tests; Q16-Q17 and Q20.

**Explain:** The lockdown comparison and its limits; the Diwali event-window question; and how station-level variation can be hidden by city averages. Then explain the paired winter-versus-monsoon t-test, the city-level A/B-style lockdown comparison, and the one-sided city-level Diwali test: hypotheses, unit of analysis, why the test was selected, p-value/confidence interval, multiple-testing adjustment where reported, decision, and limits. Make clear that observational comparisons do not prove causality.

**Core takeaway:** Report the strength and limits of evidence, not just the direction of an observed difference. A non-significant result is not proof of no effect.

## Presenter 4 - Temporal persistence and predictive model

**Notebook material:** Q12, Q15; Part 4 (Linear Regression, evaluation tables, error comparison and diagnostic charts); Q18-Q19; final conclusion.

**Explain:** Whether bad-air days occur in streaks (Q12), how yesterday's AQI relates to today's (Q15), why next-day AQI is a regression task, the target and previous-day predictors, preprocessing pipeline, chronological train/validation/2020 holdout split, feature-set selection, and persistence baseline. Explain why statistical test p-values are not fed to the model, how the seasonal finding informs calendar features, and why unsupported event flags are excluded. Compare MAE, RMSE, MAPE, R-squared, and signed error; interpret the relative-to-persistence chart; then explain the city and AQI-band diagnostics, including the Ahmedabad anomaly and sparse extreme-AQI bands. Close with Q18-Q19 and the study's conclusion and limitations. Q19 has been replaced with a model error-diagnostics question. Part 5 (BI/dashboard handoff) is intentionally outside this presentation split.

**Core takeaway:** Linear Regression satisfies the course requirement and beats persistence on RMSE and R-squared, but not on MAE or MAPE. Its errors vary by city and AQI range, so report mixed performance and diagnostic limitations rather than claiming it is uniformly better.

## Visualization deliverable (outside the four notebook roles)

The case-study instructions ask for a suitable Tableau, Power BI, or Python visualization. Include a visualization on the presentation's visualization slide. Since the project has a dashboard, you may show a screenshot or a brief live view; no presenter needs to explain the notebook's Part 5 build guide or BI export code.

## Shared presentation expectations

- Use the notebook's own plots, tables, test outputs, and model metrics as evidence; do not introduce unsupported claims.
- For every analysis question, state what was compared, what the visual/test shows, and the qualified conclusion.
- Coordinate transitions: Presenter 1 hands off data limitations; Presenter 2 shows patterns; Presenter 3 tests selected claims; Presenter 4 explains prediction and summarizes the decision.
- All presenters should know the dataset's uneven city/year coverage, partial 2020 period, Ahmedabad anomaly, observational design, and the distinction between association and causation.
