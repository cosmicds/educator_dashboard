import solara
import plotly.express as px
import plotly.graph_objects as go

from collections import Counter

from numpy import nanmin, nanmax, isnan

def matching_cols(df, val, col, count = None):
    """
    Return a dictionary of columns and values for a given value of a column
    """
 
    out = {c:df[c][df[col]==val].to_list() for c in df.columns}
    out.update({'count':count or len(out[col])})
    out.update({col:val})
    return out

def aggregrate(dataframe, col):
    vals = Counter(dataframe[col])
    return {v:matching_cols(dataframe, v, col, count)  for v,count in vals.items()}


@solara.component
def AgeHoHistogram(data, which = 'age', subset = None, subset_label = None, main_label = None, subset_color = '#0097A7', main_color = '#BBBBBB', title = None):
    # subset is boolean array which take subset of data
    
    # manual aggregation. instead use pandas groupby and agg
    # df_agg = DataFrame(aggregrate(data, which)).T
    # df_agg.sids = df_agg.sids.apply(lambda x:'<br>' + '<br>'.join(x))
    def sids_agg(sids):
        return '<br>'+ '<br>'.join(sids)
    def name_agg(names):
        return '<br>'+ '<br>'.join(names)
    

    df_agg = data.groupby(which, as_index=False).agg(count=(which,'size'), student_id = ('student_id', sids_agg), name = ('name', name_agg))
    # add single valued column
    df_agg['group'] = 'Full Class'
    if len(df_agg) == 0:
        xmin, xmax = 0, 1
    else:
        xmin, xmax = nanmin(df_agg[which]), nanmax(df_agg[which])

    labels = {'age':'Age of Universe (Gyr)', 'student_id':'Student', 'name': 'Student', 'h0':'Hubble Constant (km/s/Mpc)'}

    fig = px.bar(data_frame = df_agg, x = which, y='count', hover_data='name', labels = labels, barmode='overlay', opacity=1)
    fig.update_traces(hovertemplate = labels[which] + ': %{x}<br>' + 'count=%{y}<br>' + labels['student_id'] + ': %{customdata}' + '<extra></extra>', width=0.8)

    if subset is None:
        main_color = subset_color
        main_label = "Full Class"

    fig.update_traces(marker_color=main_color)
    fig.add_trace(go.Bar(x=[None], y=[None], name = main_label, marker_color = main_color))
    title = f'Class {which.capitalize()}<br>Distribution' if title is None else title
    fig.update_layout(showlegend=True, title_text=title, xaxis_showgrid=False, yaxis_showgrid=False, plot_bgcolor="white")
    # show only integers on y-axis
    fig.update_yaxes(tick0=0, dtick=1, linecolor="black")
    # show ticks every 1
    fig.update_xaxes(range=[xmin-1.5, xmax+1.5], linecolor="black")
    
    if subset is not None:
        data_subset = data[subset]
        df_agg_subset = data_subset.groupby(which, as_index=False).agg(count=(which,'size'), student_id = ('student_id', sids_agg))
        bar = go.Bar(x=df_agg_subset[which], y=df_agg_subset['count'],
                     name=subset_label, 
                     opacity=1, 
                     width=0.8,
                     marker_color=subset_color,
                     hoverinfo='skip', 
                     customdata=df_agg_subset['student_id'])
        bar.hovertemplate = labels[which] + ': %{x}<br>' + 'count=%{y}<br>' + labels['student_id'] + ': %{customdata}' + '<extra></extra>'
        
        fig.add_trace(bar)
        # show legend
    # fig.update_layout(showlegend=True)
    fig.update_layout(
        legend = dict(
            orientation="v",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=1,
            bordercolor="#444",
            borderwidth=0,
            bgcolor='#efefef',
            itemclick = False,
            itemdoubleclick = False,
            font=dict(size=11),
        ),
        margin=dict(l=0, r=25, t=50, b=0),
        title = dict(
            xref='container',
            x=0.05,
            xanchor='left',
            yref='container',
            yanchor='top',
            y=.95,
        )
    )
    
    

    solara.FigurePlotly(fig)