import solara

from .Repeater import Repeater

@solara.component

def refresh_class(roster, student_names):
    print(f"refreshing class data class id: {roster.value.class_id}")
    r = roster.value.empty_copy()
    if student_names is not None:
        student_names_dict = {row['student_id']: row['name'] for _, row in student_names.iterrows()}
        r.set_student_names(student_names_dict)
    roster.set(r)

@solara.component
def RefreshClass(rate_minutes = 5, on_refresh = None, roster = None, student_names = None):
    print("**** refresh class component ****")
    if on_refresh is None:
        def on_refresh():
            print('refreshing class data')
            return refresh_class(roster, student_names)

    print("refresh class component")

    refreshRate = rate_minutes * 60 * 1000
    Repeater(periodInMilliseconds=refreshRate, 
            on_refresh=on_refresh, 
            show_refresh_button=True, 
            stop_start_button=True, 
            icon_only=True,
            _show_debug=False)