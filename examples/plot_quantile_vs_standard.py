"""
Quantile Regression Forests vs. Random Forests
==============================================

This example compares the predictions generated by a quantile regression
forest (QRF) and a standard random forest regressor (RF) on a synthetic
right-skewed dataset. In a right-skewed distribution, the mean is to the right
of the median. This example demonstrates how the median (quantile = 0.5)
predicted by a quantile regressor (QRF) can be a more reliable estimator than
the mean predicted by a standard random forest when dealing with skewed
distributions.
"""

import altair as alt
import numpy as np
import pandas as pd
import scipy as sp
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from quantile_forest import RandomForestQuantileRegressor

random_state = np.random.RandomState(0)
quantiles = np.linspace(0, 1, num=101, endpoint=True).round(2).tolist()

# Create right-skewed dataset.
n_samples = 5000
a, loc, scale = 7, -1, 1
skewnorm_rv = sp.stats.skewnorm(a, loc, scale)
skewnorm_rv.random_state = random_state
y = skewnorm_rv.rvs(n_samples)
X = random_state.randn(n_samples, 2) * y.reshape(-1, 1)

regr_rf = RandomForestRegressor(random_state=random_state)
regr_qrf = RandomForestQuantileRegressor(random_state=random_state)

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=random_state)

regr_rf.fit(X_train, y_train)
regr_qrf.fit(X_train, y_train)

y_pred_rf = regr_rf.predict(X_test)  # standard RF predictions (mean)
y_pred_qrf = regr_qrf.predict(X_test, quantiles=quantiles)  # QRF predictions (quantiles)

legend = {
    "Actual": "#c0c0c0",
    "RF (Mean)": "#f2a619",
    "QRF (Median)": "#006aff",
}


def format_frac(fraction):
    return f"{fraction:.3g}".rstrip("0").rstrip(".") or "0"


df = pd.DataFrame(
    {
        "actual": y_test,
        "rf": y_pred_rf,
        **{f"qrf_{format_frac(q_i)}": y_i.ravel() for q_i, y_i in zip(quantiles, y_pred_qrf.T)},
    }
)


def plot_prediction_histograms(df, legend):
    # Slider for varying the quantile value used for generating the QRF histogram.
    slider = alt.binding_range(
        name="Predicted Quantile: ",
        min=0,
        max=1,
        step=0.5 if len(quantiles) == 1 else 1 / (len(quantiles) - 1),
    )
    quantile_val = alt.param(value=0.5, bind=slider, name="quantile")

    click = alt.selection_point(bind="legend", fields=["label"], on="click")

    chart = (
        alt.Chart(df)
        .add_params(quantile_val, click)
        .transform_calculate(qrf_col="'qrf_' + quantile")
        .transform_calculate(qrf="datum[datum.qrf_col]")
        .transform_calculate(calculate="round(datum.actual * 10) / 10", as_="Actual")
        .transform_calculate(calculate="round(datum.rf * 10) / 10", as_="RF (Mean)")
        .transform_calculate(calculate="round(datum.qrf * 10) / 10", as_="QRF (Quantile)")
        .transform_fold(["Actual", "RF (Mean)", "QRF (Quantile)"], as_=["label", "value"])
        .mark_bar()
        .encode(
            x=alt.X(
                "value:N",
                axis=alt.Axis(
                    labelAngle=0,
                    labelExpr="datum.value % 0.5 == 0 ? datum.value : null",
                ),
                title="Actual and Predicted Target Values",
            ),
            y=alt.Y("count():Q", axis=alt.Axis(format=",d", title="Counts")),
            color=alt.condition(
                click,
                alt.Color("label:N", sort=list(legend.keys()), title=None),
                alt.value("lightgray"),
            ),
            opacity=alt.condition(click, alt.value(1), alt.value(0.5)),
            xOffset=alt.XOffset("label:N"),
            tooltip=[
                alt.Tooltip("label:N", title="Label"),
                alt.Tooltip("value:Q", title="Value (binned)"),
                alt.Tooltip("count():Q", format=",d", title="Counts"),
            ],
        )
        .configure_range(category=alt.RangeScheme(list(legend.values())))
        .properties(
            title="Distribution of QRF vs. RF Predictions on Right-Skewed Distribution",
            height=400,
            width=650,
        )
    )
    return chart


chart = plot_prediction_histograms(df, legend)
chart
