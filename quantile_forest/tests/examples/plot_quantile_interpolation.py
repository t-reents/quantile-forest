"""
Comparing Quantile Interpolation Methods
========================================

An example illustration of the interpolation methods that can be applied
during prediction when the desired quantile lies between two data points. In
this toy example, the forest estimator creates a single split that separates
samples 1–3 and samples 4–5, with quantiles calculated separately for these
two groups based on the actual sample values. The interpolation methods are
used when a calculated quantile does not precisely correspond to one of the
actual values.
"""

import altair as alt
import numpy as np
import pandas as pd

from quantile_forest import RandomForestQuantileRegressor

interpolations = {
    "Linear": "#006aff",
    "Lower": "#ffd237",
    "Higher": "#0d4599",
    "Midpoint": "#f2a619",
    "Nearest": "#a6e5ff",
}

# legend = {"Actual": "#000000"} | interpolations
legend = {"Actual": "#000000"}
legend.update(interpolations)

# Create toy dataset.
X = np.array([[-1, -1], [-1, -1], [-1, -1], [1, 1], [1, 1]])
y = np.array([-2, -1, 0, 1, 2])

est = RandomForestQuantileRegressor(
    n_estimators=1,
    max_samples_leaf=None,
    bootstrap=False,
    random_state=0,
)
est.fit(X, y)

# Initialize data with actual values.
data = {
    "method": ["Actual"] * len(y),
    "x": [f"Sample {idx + 1} ({x})" for idx, x in enumerate(X.tolist())],
    "y_med": y.tolist(),
    "y_low": y.tolist(),
    "y_upp": y.tolist(),
}

# Populate data based on prediction results with different interpolations.
for interpolation in interpolations:
    y_pred = est.predict(X, quantiles=[0.025, 0.5, 0.975], interpolation=interpolation.lower())

    data["method"].extend([interpolation] * len(y))
    data["x"].extend([f"Sample {idx + 1} ({x})" for idx, x in enumerate(X.tolist())])
    data["y_low"].extend(y_pred[:, 0])
    data["y_med"].extend(y_pred[:, 1])
    data["y_upp"].extend(y_pred[:, 2])

df = pd.DataFrame(data)


def plot_interpolations(df, legend):
    click = alt.selection_point(fields=["method"], bind="legend")

    color = alt.condition(
        click,
        alt.Color("method:N", sort=list(legend.keys()), title=None),
        alt.value("lightgray"),
    )

    tooltip = [
        alt.Tooltip("method:N", title="Method"),
        alt.Tooltip("x:N", title="X Values"),
        alt.Tooltip("y_med:N", format=".3f", title="Median Y Value"),
        alt.Tooltip("y_low:N", format=".3f", title="Lower Y Value"),
        alt.Tooltip("y_upp:N", format=".3f", title="Upper Y Value"),
    ]

    point = (
        alt.Chart(df, width=alt.Step(20))
        .mark_circle(opacity=1, size=75)
        .encode(
            x=alt.X(
                "method:N",
                axis=alt.Axis(labels=False, tickSize=0),
                sort=list(legend.keys()),
                title=None,
            ),
            y=alt.Y("y_med:Q", title="Actual and Predicted Values"),
            color=color,
            tooltip=tooltip,
        )
    )

    area = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                "method:N",
                axis=alt.Axis(labels=False, tickSize=0),
                sort=list(legend.keys()),
                title=None,
            ),
            y=alt.Y("y_low:Q", title=""),
            y2=alt.Y2("y_upp:Q", title=None),
            color=color,
            tooltip=tooltip,
        )
    )

    chart = (
        (area + point)
        .add_params(click)
        .properties(height=400)
        .facet(
            column=alt.Column(
                "x:N",
                header=alt.Header(labelOrient="bottom", titleOrient="bottom"),
                title="Samples (Feature Values)",
            )
        )
        .configure_facet(spacing=15)
        .configure_range(category=alt.RangeScheme(list(legend.values())))
        .configure_scale(bandPaddingInner=0.9)
        .configure_view(stroke=None)
    )

    return chart


chart = plot_interpolations(df, legend)
chart
