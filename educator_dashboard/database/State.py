
import warnings
warnings.filterwarnings('ignore') # ignore warnings

from .markers import markers

from numpy import nan
class State:
    markers = markers
    

    def __init__(self, story_state):
        # list story keys
        self.name = story_state.get('name','') # string
        self.title = story_state.get('title','') # string
        self.stages = {k:v.get('state',{}) for k,v in story_state['stages'].items()} #  dict_keys(['0', '1', '2', '3', '4', '5', '6'])
        class_room_keys = ['id', 'code', 'name', 'active', 'created', 'updated', 'educator_id', 'asynchronous']
        self.classroom = story_state.get('classroom',{k:None for k in class_room_keys})# dict_keys(['id', 'code', 'name', 'active', 'created', 'updated', 'educator_id', 'asynchronous'])
        self.responses = story_state.get('responses',{})
        self.mc_scoring = story_state.get('mc_scoring',{}) # dict_keys(['1', '3', '4', '5', '6'])
        self.stage_index = story_state.get('stage_index',nan) # int
        self.total_score = story_state.get('total_score',nan) #int
        self.student_user = story_state.get('student_user',{}) # dict_keys(['id', 'ip', 'age', 'lat', 'lon', 'seed', 'dummy', 'email', 'gender', 'visits', 'password', 'username', 'verified', 'last_visit', 'institution', 'team_member', 'last_visit_ip', 'profile_created', 'verification_code'])
        self.teacher_user = story_state.get('teacher_user',None) # None
        self.max_stage_index = story_state.get('max_stage_index',0) # int
        self.has_best_fit_galaxy = story_state.get('has_best_fit_galaxy',False) # bool
        
        
    
    def get_possible_score(self):
        possible_score = 0
        for key, value in self.mc_scoring.items():
            for v in value.values():
                possible_score += 10
        return possible_score
    
    def stage_score(self, stage):
        score = 0
        possible_score = 0
        if str(stage) not in self.mc_scoring:
            return score, possible_score
        for key, value in self.mc_scoring[str(stage)].items():
            if value is None:
                score += 0
            else:
                v = value.get('score',0)
                if v is None:
                    score += 0
                else:
                    score += v
            # score += (value.get('score',0) or 0)
            
            possible_score += 10
        return score, possible_score
    

    @property
    def how_far(self):
        stage_index = self.max_stage_index
        if stage_index is nan:
            return {'string': 'No stage index', 'value':0.0}
        stage_markers = self.markers.get(str(stage_index),None)
        
        frac = self.stage_fraction_completed(stage_index)
        # are we in slideshow stage
        if stage_markers is None:
            string_fmt =  "In Stage {} slideshow".format(stage_index)
        else:
            string_fmt = f"{frac:.0%} through Stage {stage_index}"
            
        return {'string': string_fmt, 'value':frac}
    
    
    def stage_fraction_completed(self, stage_index):
        return self.stage_progress(stage_index)['percent']
    
    def stage_progress(self, stage_index):
        if stage_index is None:
            return {'percent':nan, 'total':0, 'current':0}
        if isinstance(stage_index, (str, int)):
            stage_index = str(stage_index)
        
        stage = self.stages.get(stage_index,{})
        
        if 'progress' in stage.keys():
            progress = {
                'percent': stage.get('progress',nan),
                'total': stage.get('n_markers',1),
                'current': stage.get('max_marker_index',1),
            }
            return progress
        else:
            markers = self.markers[str(stage_index)]
            if markers is None:
                return {'percent':1, 'total':1, 'current':1}
            current_stage_marker = self.stages[str(stage_index)]['marker']
            total = len(markers)
            if current_stage_marker not in markers:
                return {'percent':nan, 'total':total, 'current':0}
            current = markers.index(current_stage_marker)
            frac = float(current) / (float(total) - 1)
            return {'percent':frac, 'total':total, 'current':current}
        
    
    @property
    def story_progress(self):
        progress = {}
        for key, value in self.stages.items():
            progress[key] = self.stage_progress(key)
        return progress
            
            
        
    
    def total_fraction_completed(self):
        total = []
        current = []
        for key, stage in self.stages.items():
            stage_progress = self.stage_progress(key)
            total.append(stage_progress['total'])
            current.append(stage_progress['current'])
        if nan in current:
            frac = nan
        else:
            total = [t-1 if t > 1 else 1 for t in total]
            frac = int(100 * float(sum(current)) / float(sum(total)))
        return {'percent':frac, 'total':sum(total), 'current':sum(current)}
    
    @property
    def possible_score(self):
        return self.get_possible_score()
    
    @property
    def score(self):
        return self.total_score / self.possible_score
    
    @property
    def story_score(self):
        total = 0
        for key, stage in self.stages.items():
            score, possible = self.stage_score(key)
            total += score
        return total
    
    @property
    def current_marker(self):
        return self.stages.get(str(self.stage_index),{}).get('marker','none')
    
    @property
    def max_marker(self):
        return self.stages.get(str(self.max_stage_index),{}).get('marker','none')
    
    @property
    def percent_completion(self):
        return self.total_fraction_completed()['percent']
    
    
# create a wrapper class StateList that can be used to create a list of State objects
# and getattr to get the attributes of the State object
class StateList():
    
    def __init__(self, list_of_states):
        self.states = [State(state) for state in list_of_states]
    
    def __getattribute__(self, __name):
        try:
            return object.__getattribute__(self, __name)
        except AttributeError:
            if __name == 'student_id' or __name == 'id':
                return [state.student_user['id'] for state in self.states]
            return [getattr(state, __name) for state in self.states]

