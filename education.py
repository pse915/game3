"""Population learning scenarios. Indicators are fictional, never population forecasts."""
from copy import deepcopy

LABELS = {'economy':'지역경제', 'learning':'교육·보육', 'jobs':'일자리 환경',
          'care':'돌봄 접근성', 'exchange':'세대 교류', 'budget':'재정 여력'}
BASE = {'economy':3,'learning':3,'jobs':3,'care':3,'exchange':3,'budget':12}
CORE = ('nursery','care','labor')

WITNESSES = {
 'nursery': [
  ('보람 · 원장','출생아 수가 줄고 젊은 주민도 떠나면서 빈 의자가 늘었어요. 학교 학급과 어린이 가게도 영향을 받아요.'),
  ('나리 · 청년','불안정한 일자리, 주거비와 돌봄 부담이 미래 계획을 어렵게 해요. 가족을 꾸리는 방식은 각자가 결정할 일이에요.'),
  ('하린 · 협의회장','교육·돌봄 여건과 일자리를 함께 개선해야 해요. 시설을 함께 쓰더라도 안전과 전문 인력이 필요해요.')],
 'care': [
  ('연주 · 돌봄 직원','고령인구 비중이 늘면서 방문 돌봄과 의료 수요가 커졌어요. 야간 근무 가족에게 맡기기에는 부담이 커요.'),
  ('정숙 · 은퇴한 목공','내 집에서 스스로 살고 싶어요. 이동이 어려운 날에는 진료와 도움이 필요하지만 목공을 가르칠 힘도 있어요.'),
  ('현서 · 노동자','일과 돌봄을 함께 이어가려면 가족뿐 아니라 직장과 지역의 지원이 필요해요. 돌봄 직원의 휴식도 지켜야 해요.')],
 'labor': [
  ('도준 · 상인','일할 연령대의 주민이 줄고 청년이 떠나면서 채용이 어려워졌어요. 영업시간을 줄여 이웃도 불편해요.'),
  ('정숙 · 숙련 주민','경험을 나누며 다시 일하고 싶어요. 건강에 맞는 시간과 새 기술을 배울 기회가 있으면 좋겠어요.'),
  ('선우 · 상담사','좋은 근로조건, 재교육과 생산성 개선을 함께 살펴야 해요. 기술 도입에도 비용과 적응 시간이 필요해요.')],
}

# Immediate effects and later-stage effects are deliberately distinct.
EFFECTS = {
 'nursery': {'together':({'learning':1,'exchange':2,'budget':-3},{'learning':1}),
             'retrain':({'jobs':1,'budget':-2},{'jobs':2}),
             'expense':({'learning':1,'budget':-2},{'learning':2})},
 'care': {'share':({'care':1,'exchange':2,'budget':-1},{}),
          'flex':({'care':1,'jobs':2,'budget':-2},{}),
          'service':({'care':3,'budget':-3},{})},
 'labor': {'retrain':({'jobs':1,'budget':-2},{'economy':2,'jobs':1}),
           'hire':({'jobs':2,'exchange':1,'budget':-2},{}),
           'rest':({'jobs':2,'care':1,'budget':-2},{'economy':1})},
 'policy': {'youth':({'jobs':1,'learning':1,'budget':-3},{'economy':2}),
            'balance':({'care':2,'learning':1,'budget':-3},{}),
            'aging':({'care':2,'exchange':1,'budget':-3},{}),
            'together':({'exchange':3,'budget':-2},{'economy':1})},
}

OUTCOMES = {
 'nursery': {
  'together':('세대가 함께 쓰는 배움터의 시범 운영을 시작했습니다. 교육 접근성과 교류가 개선되지만 예산 3칸과 전문 인력이 필요합니다. 출생아 수가 곧바로 늘지는 않습니다.', '공동 배움터 시범 운영', '교사: 세대 수업을 시작했어요. 참여하지 못하는 가정과 안전 기준도 살펴야 해요.'),
  'retrain':('교직원 전환 교육을 시작했습니다. 일자리 환경을 돕지만 예산 2칸이 들고 훈련 효과에는 시간이 필요합니다. 아이들의 기존 교육 기회도 지켜야 합니다.', '교직원 재교육 접수', '보람: 훈련을 마친 교직원이 새 역할을 찾았어요. 어린이 교육을 맡을 인력도 계속 필요해요.'),
  'expense':('양육·교육비 부담을 조사하고 비용 지원 시범사업을 마련했습니다. 교육 접근성을 돕지만 예산 2칸이 들고 고용·주거 문제도 남습니다. 출산은 개인의 선택입니다.', '교육비 지원 시범 운영', '청년 주민: 비용 부담이 줄었지만 안정적인 일자리와 집도 중요해요.')},
 'care': {
  'share':('주민이 가능한 시간에 돌봄을 나눕니다. 교류와 돌봄 접근성이 개선되고 예산 1칸이 듭니다. 전문 의료를 대신할 수 없고 참여자의 휴식이 필요합니다.', '공동 돌봄 시간표', '정숙: 도움을 받고 목공 수업도 나눠요. 아픈 날에는 전문적인 지원이 필요해요.'),
  'flex':('직장과 근무시간 조정을 협의합니다. 일자리 환경과 돌봄 접근성을 돕지만 예산 2칸과 사업장의 조율이 필요합니다. 가족에게만 책임을 맡길 수는 없습니다.', '돌봄 근무 조정 안내', '현서: 돌봄 시간을 확보했어요. 조정이 어려운 직장과 가족도 지원해야 해요.'),
  'service':('방문 돌봄·진료 연계를 시범 운영합니다. 돌봄 접근성이 개선되지만 예산 3칸과 돌봄 인력 확보가 필요합니다. 주민의 독립적인 생활 의사를 존중합니다.', '방문 돌봄·진료 접수', '연주: 방문 지원이 연결됐어요. 대기 주민과 종사자의 휴식을 계속 챙겨야 해요.')},
 'labor': {
  'retrain':('세대별 기술 교육을 시작했습니다. 예산 2칸이 들며 숙련과 새 기술이 연결되는 효과는 다음 생애 시기에 확인합니다. 교육 중에도 가게 운영을 지원해야 합니다.', '기술 교육 모집', '도준: 훈련 뒤 새 기술을 적용했어요. 모든 가게가 같은 속도로 적응하지는 못해요.'),
  'hire':('건강과 희망에 맞는 시간제 일자리를 마련합니다. 일자리와 교류가 개선되지만 예산 2칸과 안전한 근로조건이 필요합니다. 모든 고령자에게 일을 요구하지 않습니다.', '희망·건강에 맞춘 채용', '정숙: 내게 맞는 시간을 골라 일해요. 일하지 않을 선택과 휴식도 존중받아요.'),
  'rest':('휴식·안전 공간과 근로조건을 개선합니다. 일자리 환경과 돌봄 접근성이 개선되지만 예산 2칸이 들고 인력 부족을 한 번에 해결하지는 못합니다.', '안전·휴식 공간 마련', '도준: 근무 환경이 나아졌어요. 채용과 생산성 개선은 계속 필요해요.')},
}

def enrich(events):
    for key in CORE:
        event = events[key]
        event['witnesses'] = [{'name':n,'text':t} for n,t in WITNESSES[key]]
        event['learning_goals'] = {'nursery':['low_birth','education_cost','housing','employment'],
                                  'care':['aging','elder_care','workcare'],
                                  'labor':['aging','labor','generations']}[key]
        # Catch-up events remain reachable for old saves already in retirement.
        event['stages'] = [1,2]
        event['free'] = True
        for option, (text, visual, followup) in OUTCOMES[key].items():
            choice = event['choices'][option]
            choice.update(text=text,visual=visual,followup=followup)
            choice['concepts'] = list(dict.fromkeys(choice['concepts']+event['learning_goals']))
    events['nursery']['title'] = '아이들이 줄어든 마을'
    events['nursery']['choices']['expense']['label'] = '양육·교육비 조사와 지원 시범사업'
    events['care']['intro'] = '돌봄센터에는 빈 시간표가, 정숙의 집에는 밀린 진료 예약이 있습니다. 주민 세 사람의 입장을 듣고 대응을 고르세요.'
    events['labor']['intro'] = '빵집의 영업시간이 줄었습니다. 주민 세 사람에게 이유와 바라는 변화를 듣고 대응을 고르세요.'
    for key, options in EFFECTS.items():
        for option,(now,later) in options.items():
            events[key]['choices'][option]['community_effects'] = now
            events[key]['choices'][option]['later_effects'] = later

def community_for(state):
    values = deepcopy(BASE)
    from content import EVENTS
    for event, decision in state.get('decisions',{}).items():
        option = decision.get('option')
        if option not in EFFECTS.get(event,{}): continue
        now,later = EFFECTS[event][option]
        for k,v in now.items(): values[k] += v
        if state.get('stage',0)>=2:
            for k,v in later.items(): values[k] += v
    return {k:max(0,min(12,v)) for k,v in values.items()}

def world_changes(state):
    from content import EVENTS
    changes=[]
    for event in CORE+('policy',):
        decision=state.get('decisions',{}).get(event)
        if not decision: continue
        choice=EVENTS[event]['choices'].get(decision.get('option'),{})
        changes.append({'event':event,'choice':choice.get('label',''),
                        'visual':choice.get('visual',choice.get('label','')),
                        'outcome':choice.get('text',''),
                        'followup':choice.get('followup',choice.get('text','')),
                        'later_ready':state.get('stage',0)>=2})
    return changes

def requirements_for(state):
    from content import REQUIRED
    required=list(REQUIRED[state['stage']])
    if state['stage']==2 and not state.get('ended'):
        required = [k for k in ('nursery','labor') if k not in state.get('decisions',{})]+required
    return required

def migrate(state):
    """Add derived fields; preserve schema, run, choices, auth, revisions and old endings."""
    result=deepcopy(state)
    result.setdefault('content_version',5)
    result.setdefault('school_records',{})
    result.setdefault('building_records',{})
    result.setdefault('guide_mode','basic')
    result['community']=community_for(result)
    result['world_changes']=world_changes(result)
    return result
