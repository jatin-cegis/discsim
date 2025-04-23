import plotly.express as px

def plot_pie_chart(labels, values, title):
    # Sort values and labels in descending order
    sorted_data = sorted(zip(values, labels), reverse=True)
    sorted_values, sorted_labels = zip(*sorted_data)
    color_map = {
        label: "#3b8e51" if "Unique" in label else "#9e2f17"
        for label in sorted_labels
    }
    fig = px.pie(
        names=sorted_labels, 
        values=sorted_values, 
        title=title,
        color=sorted_labels,
        color_discrete_map=color_map)
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=400,
        showlegend= True
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_100_stacked_bar_chart(data, x, y, color, title, x_label, y_label):
    fig = px.bar(data, x=x, y=y, color=color, title=title, 
                labels={x: x_label, 'value': y_label},
                barmode='relative')  # This makes it a 100% stacked bar chart
    
    fig.update_layout(legend_title_text='')
    return fig
