import solara

import plotly.express as px
import plotly.graph_objects as go

@solara.component
def ClassPlot(dataframe, 
            x_col = "est_dist_value", 
            y_col = "velocity_value", 
            label_col = "student_id", 
            xy_label = {"x":{'label': 'Distance', 'units': 'Mpc'}, "y":{'label': 'Velocity', 'units': 'km/s'}},
            on_click = None,
            select_on = None,
            selected = solara.reactive(None),
            allow_click = True,
            subset = None,
            subset_label = None,
            main_label = None,
            subset_color='#0097A7',
            main_color='#BBBBBB',
              ):
    
    
    print('Generating Class Plot')
    
    if select_on is None:
        select_on = "student_id"
    
    if dataframe is None:
        solara.Markdown("No data")
        return 
    
    config = {
            'remove': [
                'zoom2d', 
                'pan2d', 
                'lasso2d', 
                'zoomIn2d', 
                'zoomOut2d',
                'autoscale'
            ]
        }
    
    
    if x_col not in dataframe.columns:
        print(f"ClassPlot: {x_col} not in dataframe")
        solara.Markdown(f"**{x_col}** not in dataframe")
        return
    
    labels =  {x_col: "{label} ({units})".format(**xy_label['x']),  
               y_col: "{label} ({units})".format(**xy_label['y'])}
    fig = px.scatter(dataframe, x=x_col, y=y_col, custom_data = label_col, labels = labels)
    
    if subset is None and selected.value is None:
        main_color = subset_color
        main_marker_size = 7
        main_label = 'Full Class'
    else:
        main_marker_size = 5
        

    fig.update_traces(marker_color=main_color, marker_size = main_marker_size)
    fig.update_layout(modebar = config, title="Class Hubble<br>Diagram", xaxis_showgrid=False, yaxis_showgrid=False, plot_bgcolor="white")
    fig.update_xaxes(linecolor='black')
    fig.update_yaxes(linecolor='black')
    # add empty trace to show on legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode = 'markers', name = main_label, marker_color = main_color, marker_size = main_marker_size))

    xlabel = xy_label["x"]['label']+': %{x:f} ' + xy_label["x"]['units']
    ylabel = xy_label["y"]['label']+': %{y:f} ' + xy_label["y"]['units']
    hovertemplate = xlabel + '<br>' + ylabel + '<br>Student: %{customdata}' 
    
    fig.update_traces(hovertemplate=hovertemplate) 
    
    def click_action(points):
        if not allow_click:
            return
        selected_index = points['points']['point_indexes'][0]
        selected.set(dataframe.iloc[selected_index][select_on])
        if on_click is not None:
            on_click(points)
        
    
    if subset is not None:
        print('Adding seen trace')
        sub_data = dataframe[subset]
        hovertemplate = '<b>%{customdata}</b><br>' + xlabel + '<br>' + ylabel
        fig.add_trace(go.Scatter(x= sub_data[x_col], y= sub_data[y_col], mode = 'markers',
                                            customdata = sub_data[label_col],
                                            hovertemplate = hovertemplate,
                                            name = subset_label,
                                            marker_symbol = 'circle',   
                                            marker_size = 7,
                                            marker_color = subset_color))
        
    if selected.value is not None:    
        print('Adding student trace')
        stud_data = dataframe[dataframe[select_on] == str(selected.value)]

        hovertemplate = '<b>%{customdata}</b><br>' + xlabel + '<br>' + ylabel
        fig.add_trace(go.Scatter(x= stud_data[x_col], y= stud_data[y_col], mode = 'markers',
                                            customdata = stud_data[label_col],
                                            hovertemplate = hovertemplate,
                                            name = str(selected.value),
                                            marker_symbol = 'circle',   
                                            marker_size = 10,
                                            marker_color = '#FF8A65'))
    
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
    
    
    return solara.FigurePlotly(fig, on_click=click_action, )
        
