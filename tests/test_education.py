import itertools, json, unittest
from copy import deepcopy
from content import EVENTS, REQUIRED, public_content
from engine import new_state, apply, recap, ready
from education import migrate, community_for, requirements_for, CORE

def send(s,kind,**extra):
    result,msg=apply(s,{'type':kind,'nonce':f"qa-{s['revision']}-{kind}-{extra.get('event_id','')}",**extra})
    assert result['revision']==s['revision']+1,msg
    return result

def youth():
    s=new_state('QA','01','가상 학생')
    for k in REQUIRED[0]:s=send(s,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))
    return send(s,'advance')

class EducationTests(unittest.TestCase):
    def test_every_core_combination_reaches_ending_with_real_outcomes(self):
        keys=REQUIRED[1]
        for choices in itertools.product(*(EVENTS[k]['choices'] for k in keys)):
            with self.subTest(choices=choices):
                s=youth()
                for k,choice in zip(keys,choices):s=send(s,'choose',event_id=k,choice_id=choice)
                self.assertTrue(ready(s))
                self.assertTrue({'low_birth','aging','labor','elder_care'}.issubset(s['concepts']))
                self.assertEqual(len(s['world_changes']),4)
                self.assertEqual(s['community'],community_for(s))
                self.assertGreaterEqual(s['community']['budget'],0)
                self.assertLess(s['community']['budget'],12)
                s=send(s,'advance')
                for k in REQUIRED[2]:s=send(s,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))
                s=send(s,'finish')
                self.assertTrue(s['ended'])
                self.assertTrue(all(c['outcome'] and c['choice'] for c in recap(s)['world_changes']))
                self.assertEqual(migrate(json.loads(json.dumps(s,ensure_ascii=False))),s)

    def test_all_retirement_combinations_reach_ending(self):
        base=youth()
        for k in REQUIRED[1]:base=send(base,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))
        base=send(base,'advance')
        for choices in itertools.product(*(EVENTS[k]['choices'] for k in REQUIRED[2])):
            s=deepcopy(base)
            for k,option in zip(REQUIRED[2],choices):s=send(s,'choose',event_id=k,choice_id=option)
            s=send(s,'finish');self.assertTrue(s['ended'])

    def test_cannot_skip_population_scenarios(self):
        s=youth()
        for k in ['care','policy']:s=send(s,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))
        rejected,msg=apply(s,{'type':'advance','nonce':'skip'})
        self.assertEqual(rejected,s)
        self.assertFalse(ready(s))

    def test_legacy_retirement_can_catch_up_without_resetting_choices(self):
        s=new_state('QA','01','旧存档');s['stage']=2;s['age']=69
        s['decisions']={'care':{'option':'share','label':'공동 돌봄','stage':1},'policy':{'option':'aging','label':'지원','stage':1}}
        s.pop('content_version');s.pop('community');s.pop('world_changes')
        old=deepcopy(s);s=migrate(s)
        self.assertEqual(s['revision'],old['revision']);self.assertEqual(s['decisions'],old['decisions'])
        self.assertEqual(s['run_id'],old['run_id']);self.assertFalse(ready(s))
        self.assertTrue({'nursery','labor'}.issubset(requirements_for(s)))
        for k in requirements_for(s):s=send(s,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))
        s=send(s,'finish');self.assertTrue(s['ended'])

    def test_legacy_ending_preserved_and_finish_not_repeated(self):
        s=new_state('QA','01','가상');s['stage']=2;s['ended']=True
        migrated=migrate(s);self.assertTrue(migrated['ended'])
        r,msg=apply(migrated,{'type':'finish','nonce':'again'});self.assertEqual(r,migrated)
        for k in ('nursery','labor'):
            migrated=send(migrated,'choose',event_id=k,choice_id=next(iter(EVENTS[k]['choices'])))

    def test_delayed_effect_waits_until_later_stage(self):
        s=youth();s=send(s,'choose',event_id='labor',choice_id='retrain')
        now=s['community']['economy'];later=deepcopy(s);later['stage']=2
        self.assertEqual(community_for(later)['economy'],now+2)
        self.assertFalse(s['world_changes'][0]['later_ready'])

    def test_invalid_choice_payloads_never_crash_or_mutate(self):
        s=new_state('QA','01','가상')
        for bad in ({'event_id':[],'choice_id':'x'},{'event_id':'career','choice_id':{}},{'event_id':'no','choice_id':'x'}):
            r,msg=apply(s,{'type':'choose','nonce':'bad',**bad});self.assertEqual(r,s)

    def test_stale_revision_and_invalid_observations_are_safe(self):
        s=youth()
        r,msg=apply(s,{'type':'choose','event_id':'care','choice_id':'share','nonce':'stale','base_revision':0})
        self.assertEqual(r,s)
        r,msg=apply(s,{'type':'choose','event_id':'care','choice_id':'share','nonce':'safe','base_revision':s['revision'],'observations':[0,0,1,2,99,{},False]})
        self.assertEqual(r['decisions']['care']['observations'],[0,1,2])

    def test_event_graph_and_educational_evidence(self):
        content=public_content()
        for stage,required in REQUIRED.items():
            for k in required:
                self.assertIn(stage,EVENTS[k]['stages'])
                self.assertTrue(any(n['event']==k for n in content['npcs']))
        for k in CORE:
            self.assertEqual(len(EVENTS[k]['witnesses']),3)
            for choice in EVENTS[k]['choices'].values():
                self.assertTrue(set(EVENTS[k]['learning_goals']).issubset(choice['concepts']))
                self.assertTrue(choice['visual']);self.assertTrue(choice['followup'])

if __name__=='__main__':unittest.main()
