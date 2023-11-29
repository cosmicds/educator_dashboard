

import pandas as pd
from .nested_dataframe import flatten
from .State import State, StateList
from .Query import QueryCosmicDSApi
import time
HUBBLE_ROUTE_PATH = "hubbles_law"

import astropy.units as u
from math import nan

class Student():
    
    student_id = None
    class_id = None
    story_state = {}
    stage_state = {}
    _data = None
    _mc_questions = {}
    _fr_questions = {}
    
    
    def __init__(self, student_id = None):
        self.student_id = student_id
        
    @property
    def data(self):
        return self._data

class Roster():
    
    def __init__(self, class_id = None, query = None):
        
        self._mc_questions = None
        self._fr_questions = None
        self._questions = None
        self._question_keys = None
        self._mc_keys = {}
        self._fr_keys = {}
        self._report = None
        self._short_report = None
        
        self._refresh = False
        
        self.class_id = class_id
        if query is None:
            self.query = QueryCosmicDSApi(class_id = class_id, story=HUBBLE_ROUTE_PATH)
        else:
            self.query = query
            query.class_id = class_id
            query.story = HUBBLE_ROUTE_PATH
        self.data = None
        self.student_data = {}
        self.class_summary = None
        self.grab_data()
        self.has_real_names = False
        self.real_names =  None
    
    def __eq__(self, other):
        if other.short_report() is None:
            return False
        return self.short_report() == other.short_report()
    
    @staticmethod
    def flatten_dict(d):
        return flatten(d)
    
    @staticmethod
    def fix_mc_scoring(roster):
        for i,student in enumerate(roster):
            count = 0
            story_state = student['story_state']
            mc_scoring = story_state['mc_scoring']
            for stage, scores in mc_scoring.items():
                for key, value in scores.items():
                    if value['tries'] == 0:
                        count += 1
                        mc_scoring[stage][key]['score'] = 10
                        mc_scoring[stage][key]['tries'] = 1
            roster[i]['story_state']['mc_scoring'] = mc_scoring
        return roster
    
    def grab_data(self):
        print('Getting roster')
        self.roster = self.query.get_roster()
        self.data = None
        
        if len(self.roster) == 0:
            self.student_id = []
            self.story_name = ''
            self.story_state = {}
            self.stages = []
            self.new_story_state = StateList([])
            self.last_modified = ''
            self.stage_index = 0
            return
        self.roster = self.fix_mc_scoring(self.roster)
        keys = self.roster[0].keys()
        new_out = self.l2d(self.roster)
        keys = new_out.keys()
        for key in keys:
            if isinstance(new_out[key][0],dict):
                new_out[key] = self.l2d(new_out[key])
            elif isinstance(new_out[key],list):
                new_out[key] = {key:new_out[key]}
            else:
                print(key, type(new_out[key][0]))
        
        self.student_id = new_out['student_id']
        self.story_name = new_out['story_name']
        self.story_state = new_out['story_state']
        
        
        keys = self.l2d(self.story_state['stages']).keys()
        self.stages = []
        def getstate(stage):
            if isinstance(stage, dict) and ('state' in stage.keys()):
                return stage['state']
            else:
                print(f'no state in class {self.class_id}')
                return {'stage':{}, 'marker':None, 'responses':[], 'mc_scores':[], 'total_score':0, 'state':{}, 'title': None}
        for key in sorted(keys):
            self.stages.append([getstate(s)  for s in self.l2d(self.story_state['stages'])[key]])
        
        
        self.new_story_state = StateList([student['story_state'] for student in self.roster])
        self.last_modified = new_out['last_modified']
        self.stage_index = self.new_story_state.stage_index
    

    @staticmethod
    def list_of_dicts_to_dict_of_lists(list_of_dicts, fill_val = None):
        # keys = list_of_dicts[0].keys()
        keys = []
        for d in list_of_dicts:
            if isinstance(d, dict):
                keys.extend([k for k in d.keys() if (k not in keys) and (k is not None)])
        
        dict_of_lists = {k: [o[k] if (hasattr(o,'keys') and (k in o.keys())) else fill_val for o in list_of_dicts] for k in keys}
        return dict_of_lists
    
    def l2d(self, list_of_dicts, fill_val = None):
        return self.list_of_dicts_to_dict_of_lists(list_of_dicts, fill_val)
    
    def get_class_data(self, refresh = False, df = False):
        if self.data is None or self._refresh or refresh:
            res = self.query.get_class_data(class_id = self.class_id)
            self.data = res if res is not None else {'student_id':[]}
            if len(self.student_data) == 0:
                groupdf = pd.DataFrame(self.data).groupby('student_id')
                for student_id in groupdf.groups.keys():
                    self.student_data[student_id] = groupdf.get_group(student_id).to_dict(orient='records')
        if df:
            return pd.DataFrame(self.data)
        return self.data
            
    
    def get_student_data(self, student_id, refresh = False, df = False):
        if (student_id not in self.student_data.keys()) or self._refresh or refresh:
            self.student_data[student_id] = self.query.get_student_data(student_id)['measurements']
        if df:
            return pd.DataFrame(self.student_data[student_id])
        return self.student_data[student_id]

    def get_class_summary(self, refresh = False):
        if self.class_summary is None or self._refresh or refresh:
            measurements = self.measurements(refresh = refresh) 
            def get_slope(x, y):
                # slope through origin
                return nan if (sum(x**2) == 0) else (sum(x*y)/sum(x**2))
            def slope2age(h0):
                return (1/(h0 * u.km/u.s/u.Mpc)).to(u.Gyr).value
            H0 = []
            Age = []
            for student in self.student_ids:
                student_data = measurements[measurements['student_id'] == student]
                if len(student_data) == 5:
                    H0.append(get_slope(student_data['est_dist_value'], student_data['velocity_value']))
                    Age.append(slope2age(H0[-1]))
                else:
                    H0.append(nan)
                    Age.append(nan)
            self.class_summary = self.make_dataframe(pd.DataFrame({'H0':H0, 'age':Age}))

        return self.class_summary
    
    def class_measurement_status(self, refresh = False):
        g = self.get_class_data(df=True, refresh = refresh).groupby('student_id')
        nodist = g.apply(lambda x:  5-sum(x['est_dist_value'] == 0)) # number of distances
        novel = g.apply(lambda x:  5-sum(x['velocity_value'] == 0)) # number of velocities
        complete = (novel == 5) & (nodist==5)
        df = pd.DataFrame({'distances': nodist, 'velocities': novel, 'complete': complete})
        m = set(df.index)
        a = set(self.student_ids)
        d = a - m # students in roster but not in class data
        for d in a - m:
            df.loc[d] = {'distances': -9999, 'velocities': -9999, 'complete':False}
        
        # summary
        summary = dict(
                num_complete = sum(df['complete']), # number of students with complete data
                num_incomplete = len(df) - sum(df['complete']), # number of students with incomplete data
                num_dist = sum(df['distances'] != -9999), # number of students with distances
                num_vel = sum(df['velocities'] != -9999), # number of students with velocities
                num_good = sum((df['distances'] != -9999) & (df['velocities'] != -9999)), # number of students with good data
                num_total = len(df), # number of students in class  
                )
        return {'summary':summary, 'status':df}
        
    
    def get_student_by_id(self, student_id):
        if student_id not in self.student_ids:
            print(f'{student_id} not in roster')
            return None
        return [student for student in self.roster if student['student_id'] == student_id][0]
    
    def make_dataframe(self, dictionary, include_student_id = True, include_class_id = True, include_username = True):
        # take the dictionary and make a dataframe
        # add self.student_ids as a column
        
        if 'student_id' not in dictionary.keys() and include_student_id:
            dictionary['student_id'] = self.student_ids
        if 'class_id' not in dictionary.keys() and include_class_id:
            dictionary['class_id'] = self.class_id
        if 'username' not in dictionary.keys() and include_username:
            dictionary['username'] = self.students['username'].values
        # if isinstance(dictionary, pd.DataFrame):
        #     return dictionary.set_index('student_id')
        
        # add cols conditionally on inclusion
        first_cols = []
        if include_student_id:
            first_cols.append('student_id')
        if include_class_id:
            first_cols.append('class_id')
        if include_username:
            first_cols.append('username')
        
        cols = first_cols + [col for col in dictionary.keys() if col not in first_cols]
        dictionary = {k:dictionary[k] for k in cols}
        # df = pd.DataFrame(dictionary).set_index('student_id')
        return pd.DataFrame(dictionary)
    

    def measurements(self, refresh = False):
        if len(self.roster) > 0:
            if self.data is None or refresh:
                self.data = self.get_class_data(refresh = refresh)
            
            return pd.DataFrame(self.data)
        else:
            return pd.DataFrame()
    
    
    def multiple_choice_questions(self):
        if (self._mc_questions is not None) and (not self._refresh):
            return self._mc_questions
        if len(self.roster) > 0:
            out = self.l2d(self.story_state['mc_scoring'])
            out.update({'student_id':self.student_ids})
            self._mc_questions = out
            return out
        else:
            return {'student_id': self.student_ids}
        
    
    def free_response_questions(self):
        if (self._fr_questions) is not None and (not self._refresh):
            return self._fr_questions
        
        if len(self.roster) > 0:
            out = self.l2d(self.story_state['responses'])
            out.update({'student_id':self.student_ids})
            self._fr_questions = out
            return out
        else:
            return {'student_id': self.student_ids}
    
    def questions(self):
        if (self._questions is not None) and (not self._refresh):
            return self._questions
        
        if len(self.roster) > 0:
            fr = self.free_response_questions()
            mc = self.multiple_choice_questions()
            df_fr = flatten(self.make_dataframe(fr, include_class_id=False, include_username=False))
            df_mc = flatten(self.make_dataframe(mc, include_class_id=False, include_username=False)).astype('Int64')
            self._questions = pd.merge(df_mc, df_fr, how='left', on='student_id')
        else:
            self._questions = pd.DataFrame({'student_id':self.student_ids})
        return self._questions
        
    
    def get_questions_text(self):
        qs = self.query.get_questions()
        if qs is None:
            print("""No questions found. Trying again after a moment.""")
            # wait 1 second
            time.sleep(1)
            qs = self.query.get_questions()
        return qs
    
    def question_keys(self, testing = False, get_all = True):
        if (self._question_keys is not None) and (not self._refresh):
            return self._question_keys
        
        self._question_keys = {}
        
        if get_all:
            questions = self.get_questions_text()
            keys = questions.keys()
            other_keys = set([c.split('.')[1] for c in self.questions().columns if '.' in c])
            keys = set(keys).union(other_keys)
        else:
            keys = set([c.split('.')[1] for c in self.questions().columns if '.' in c])
        
        for k in keys:
            if testing:
                q = {'text': 'Fake Long '+k, 'shorthand': 'Fake Short '+k}
            elif (k not in questions.keys()):
                print(f'{k} not in question database')
                nice_tag = ' '.join(k.replace('_', ' ').replace('-', ' ').split())
                q = {'text': 'Not in Question Database', 'shorthand': f'Not in Database ({nice_tag})'}
            else:
                q = questions[k]
            
            if q is not None:
                nice_tag = ' '.join(k.replace('_', ' ').replace('-', ' ').split())
                nice_tag = nice_tag[0].upper() + nice_tag[1:]
                
                short = q['shorthand']
                if short == '':
                    short = nice_tag
                self._question_keys[k] = {'text':q['text'], 'shorttext':short, 'nicetag': nice_tag}
                
        return self._question_keys
    
    def get_question_text(self, key):
        if key in self.question_keys().keys():
            return self.question_keys()[key]
        else:
            print(f'{key} not in question database')
            return {'text': 'Not in Question Database', 'shorttext': 'Not Available', 'nicetag': key}
                
    def mc_question_keys(self): 
        mc = self.multiple_choice_questions()
        for stage in mc.keys():
            if stage == 'student_id':
                continue
            keys = self._mc_keys.get(stage, [])
            for s in mc[stage]:
                if s is not None:
                    for q in s.keys():
                        if q not in keys:
                            keys.append(q)
                    self._mc_keys[stage] = keys
        return self._mc_keys
    
    def fr_question_keys(self):
        fr = self.free_response_questions()
        for stage in fr.keys():
            if stage == 'student_id':
                continue
            keys = self._fr_keys.get(stage, [])
            for s in fr[stage]:
                if s is not None:
                    for q in s.keys():
                        if q not in keys:
                            keys.append(q)
                    self._fr_keys[stage] = keys
                
        return self._fr_keys
    
    @property
    def student_ids(self):
        if len(self.roster) > 0:
            return [student['student_id'] for student in self.roster]
        else:
            return []
        
    def set_student_names(self, student_names = None):
        """
        student_names is a dictionary of student_id: name
        """
        if len(self.roster) > 0:
            for student in self.roster:
                if student_names is None:
                    # use random string
                    student['student']['name'] = 'Student '+str(student['student_id'])
                    # student['student']['name'] = student['username']
                else:
                    student['student']['name'] = student_names.get(student['student_id'], 'Student '+str(student['student_id']))
                    
            # if student_names is not None:
        self.has_real_names = True
        self.real_names = student_names
    
    def get_student_name(self, sid = None):
        if sid is None:
            return 'None'
        if len(self.roster) > 0:
            index = self.student_ids.index(sid) if sid in self.student_ids else None
            if index is not None:
                return self.roster[index]['student'].get('name', str(sid))
            else:
                print(f'{sid} not in roster')
        
        return str(sid)
    
    @property
    def responses(self):
        if len(self.roster) > 0:
            df = pd.DataFrame([student['story_state']['responses'] for student in self.roster])
            return self.make_dataframe(flatten(df))
        else:
            return self.make_dataframe(pd.DataFrame())
    
    def convert_column_of_dates_to_datetime(self, dataframe_column):
        return pd.to_datetime(dataframe_column).dt.tz_convert('US/Eastern').dt.strftime("%Y-%m-%d %H:%M:%S (Eastern)")
    
    @property
    def students(self):
        if len(self.roster) > 0:
            students = self.l2d([student['student'] for student in self.roster])
            return self.make_dataframe(students)
        else:
            return pd.DataFrame({'student_id':[], 'username':[], 'class_id':[]})
    
    @property
    def student_names(self):
        return [self.get_student_name(sid) for sid in self.student_ids]
    
    @property
    def out_of(self):
        if len(self.roster) == 0:
            return
        out_of = []
        for student in self.roster:
            state = State(student['story_state'])
            state.mc_scoring
            out_of.append(state.get_possible_score())
        return out_of
    
    @property
    def student_scores(self):
        if len(self.roster) == 0:
            return None
        scores = []
        for student in self.roster:
            state = State(student['story_state'])
            scores.append(state.story_score)
        return scores
    
    def fraction_completed(self):
        # for each stage, create a state object using their story_state
        how_far = []
        tot_perc = []
        for student in self.roster:
            state = State(student['story_state'])
            how_far.append(state.how_far)
            tot_perc.append(state.percent_completion)
        return self.l2d(how_far)['string'], tot_perc
    
    def report(self, refresh = False, for_teacher = True):
        "refreshing data"
        
        if self._report is not None and not self._refresh and not refresh:
            return self._report
        
        if self._refresh:
            self.grab_data()

        roster = self
        if len(roster.roster) == 0:
            return None
        if hasattr(roster,'stages') and (not for_teacher):
            data = [[s.get('marker',None) for s in stage] for stage in roster.stages]
            cols = ['Stage 1 marker', 'Stage 3 marker', 'Stage 4 marker', 'Stage 5 marker', 'Stage 6 marker']
            c1 = {k:v for k,v in zip(cols, data)}
            df = pd.DataFrame(c1)
            df['student_id'] = roster.student_id['student_id']
        else:
            df = pd.DataFrame({'student_id':roster.student_id['student_id']})
       
        
        df['student_id'] = roster.student_id['student_id']
        # add a string column containing roster.students['username']
        df['username'] = roster.students['username'].values
        if 'name' in roster.students.columns:
            df['name'] = roster.students['name'].values
        df['class_id'] = roster.class_id
        completion_string, completion_percent = roster.fraction_completed()
        df['progress'] = completion_string
        df['percent_story_complete'] = completion_percent
        # df['percent_story_complete'] = df['percent_story_complete'].apply(lambda x: int(x))
        df['max_stage_index'] = roster.new_story_state.max_stage_index
        df['max_stage_marker'] = roster.new_story_state.max_marker
        df['stage_index'] = roster.stage_index
        df['total_score'] = roster.student_scores
        df['out_of_possible'] = roster.out_of
        summ = roster.get_class_summary()
        df['Hubble_Constant'] = summ['H0'].apply(lambda x: round(x,2))
        df['Age'] = summ['age'].apply(lambda x: round(x,2))
        
        response = flatten(pd.DataFrame(roster.story_state['responses']))
        response['student_id'] = roster.student_id['student_id']
        df = df.merge(response, on='student_id', how='left')
        last_modified = pd.to_datetime(roster.last_modified['last_modified']).tz_convert('US/Eastern').strftime("%Y-%m-%d %H:%M:%S (Eastern)") # in Easterm time
        df['last_modified'] = last_modified
        
        self._report = df
        
        return df
    
    def short_report(self, refresh = False):
        if self._short_report is not None and not self._refresh and not refresh:
            return self._short_report
        
        if self._refresh:
            self.grab_data()
        
        roster = self
        if len(roster.roster) == 0:
            return None
        if hasattr(roster,'stages'):
            data = [[s.get('marker',None) for s in stage] for stage in roster.stages]
            cols = ['Stage 1 marker', 'Stage 3 marker', 'Stage 4 marker', 'Stage 5 marker', 'Stage 6 marker']
            c1 = {k:v for k,v in zip(cols, data)}
            df = pd.DataFrame(c1)
            df['student_id'] = roster.student_id['student_id']
        else:
            df = pd.DataFrame({'student_id':roster.student_id['student_id']})

        # add a string column containing roster.students['username']
        df['username'] = roster.students['username'].values
        if 'name' in roster.students.columns:
            df['name'] = roster.students['name'].values
        df['class_id'] = roster.class_id
        completion_string, completion_percent = roster.fraction_completed()
        df['progress'] = completion_string
        df['percent_story_complete'] = completion_percent
        # df['percent_story_complete'] = df['percent_story_complete'].apply(lambda x: int(x))
        df['max_stage_index'] = roster.new_story_state.max_stage_index
        df['max_stage_marker'] = roster.new_story_state.max_marker
        df['stage_index'] = roster.stage_index
        # df['total_score'] = roster.story_state['total_score']
        df['total_score'] = roster.student_scores
        df['out_of_possible'] = roster.out_of
        summ = roster.get_class_summary()
        df['Hubble_Constant'] = summ['H0'].apply(lambda x: round(x,2))
        df['Age'] = summ['age'].apply(lambda x: round(x,2))

        last_modified = pd.to_datetime(roster.last_modified['last_modified']).tz_convert('US/Eastern').strftime("%Y-%m-%d %H:%M:%S (Eastern)") # in Easterm time
        df['last_modified'] = last_modified
        
        self._short_report = df
        
        return df
    
    def refresh_data(self):
        self._refresh = True
        print('****** Refreshing data ******')
        print(' >>> Grabbing class states')
        self.grab_data()
        print(' >>> Getting questions')
        self.question_keys()
        print(' >>> Getting class data')
        self.get_class_data()
        self._refresh = False
    
    def empty_copy(self):
        return Roster(class_id = self.class_id)



## create a cli so that will take the class_id as an argument, pass it to create report and export 
# an excel fill called class_id_class_progress.xlsx

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create a report for a class')
    parser.add_argument('class_id', type=int, help='The class id')
    # if there are multiple arguments given then loop over them 
    args = parser.parse_args()
    
    if args.class_id is None:
        print('Please provide a class id')
        exit()
    
    roster = Roster(class_id = args.class_id)
    df = roster.report()#rgs.class_id)
    df.to_excel(f'{args.class_id}_class_progress.xlsx')