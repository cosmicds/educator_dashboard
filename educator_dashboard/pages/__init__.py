
import solara
from ..database.Query import QueryCosmicDSApi
from ..educator_dashboard import EducatorDashboard
from ..components.TeacherCodeInput import class_query_res



@solara.component
def ValidateEducatorCode(educator_code, class_id, dev_mode=False):
    query = QueryCosmicDSApi()
    if class_id is not None:
        class_id = int(class_id)
    if educator_code is not None:
        educator_code = int(educator_code)
    
    if educator_code is None and query.in_dev_mode():
        solara.Warning(f"Running in dev mode with class_id {class_id}")
    elif educator_code is None:
        solara.Error("No educator code provided")
        return
    else: # educator_code provided
        class_list = query.get_class_for_teacher(educator_code)['classes']
        
        # if no classes are found for the educator code, show an error message
        if len(class_list) == 0:
            educator_info = query.get_teacher_info(educator_code)['educator']
            with solara.Card():
                solara.Error(f"No classes found for educator code: {educator_code}", color="error")
                solara.Markdown(f"""
                            No classes found for educator code: {educator_code}\n
                            Educator Info: \n
                            - Name: {educator_info['first_name']} {educator_info['last_name']} \n
                            - id: {educator_info['id']}\n
                            - Email: {educator_info['email']}"""
                            )
                solara.Text(f"{class_list}")
            return
        
        
        # go to provided class id else the first class id
        if any(class_id == x.get('id', -999) for x in class_list):
            pass
        else:
            if (class_id is not None):
                solara.Error(f"Invalid class id {class_id} provided for educator code: {educator_code}", color="error")
                return
            else:
                solara.Warning(f"No class id provided. Using first class found for educator code: {educator_code}", color="error")
        

@solara.component
def Page():
    query = QueryCosmicDSApi()
    router = solara.use_router()
    if router.search is not None:
        url_params = {x.split("=")[0]: x.split("=")[1] for x in router.search.split("&")}
    else:
        url_params = {}
    
    educator_code = int(url_params["edu"]) if "edu" in url_params else None
    class_list = []
    if educator_code is not None:
        class_list = query.get_class_for_teacher(educator_code)['classes']
    solara.lab.ThemeToggle()
    ValidateEducatorCode(educator_code, url_params.get("id"), query.in_dev_mode())
    if educator_code is None and query.in_dev_mode():
        class_list = class_query_res
    EducatorDashboard(url_params, class_list)  # Call the EducatorDashboard component to render it


# The following line is required only when running the code in a Jupyter notebook:
Page()
