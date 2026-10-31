"""Small project-scoped experience pool; no model calls or implicit global transfer."""
import copy
import project_manager as pm

CATEGORIES = {'missing_rule', 'routing_failure', 'misleading_rule', 'execution_failure', 'helped', 'no_effect'}


def validate_card(card: dict) -> None:
    if not pm.ID.fullmatch(card.get('id','')):raise ValueError('Invalid rule id')
    for key,limit in [('description',500),('exclude',500),('body',4000)]:
        value=card.get(key)
        if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('Invalid rule '+key)
    if card.get('scope') not in {'project','general'}:raise ValueError('Invalid scope')
    if not isinstance(card.get('tags'),list) or not card['tags'] or any(not isinstance(t,str) or not t for t in card['tags']):raise ValueError('Explicit routing tags required')
    if not isinstance(card.get('evidence'),list) or not card['evidence']:raise ValueError('Rule needs evidence')


def recall(cards: list[dict], tags: list[str]) -> list[dict]:
    """Return bounded candidate headers; the host decides applicability/exclusions."""
    ranked=sorted(cards,key=lambda c:(-len(set(c['tags'])&set(tags)),c['id']))
    return [{k:c[k] for k in ('id','description','exclude','tags')} for c in ranked if set(c['tags'])&set(tags)][:8]


def update_memory(cards: list[dict], operations: list[dict], losses: list[dict], reads: list[dict]) -> list[dict]:
    pool={c['id']:copy.deepcopy(c) for c in cards}
    if len(pool)!=len(cards):raise ValueError('Duplicate existing cards')
    for card in cards:validate_card(card)
    evidence={l['id']:l for l in losses}
    if len(evidence)!=len(losses):raise ValueError('Duplicate loss ids')
    seen={(r['case_id'],r['rule_id']) for r in reads if r.get('kind')=='pipeline_applied_rule'}
    for loss in losses:
        if loss['category'] not in CATEGORIES:raise ValueError('Unknown attribution')
        for rid in loss['rule_ids']:
            if rid not in pool:raise ValueError('Unknown attributed rule')
            read=(loss['case_id'],rid) in seen
            if loss['category'] in {'misleading_rule','execution_failure','helped','no_effect'} and not read:raise ValueError('Attribution needs read trace')
            if loss['category']=='routing_failure' and read:raise ValueError('Routing failure conflicts with read trace')
    for op in operations:
        action=op['action'];card=copy.deepcopy(op['card']);validate_card(card);rid=card['id']
        if action not in {'create','correct','reinforce','merge'}:raise ValueError('Unknown operation')
        if (action=='create')==(rid in pool):raise ValueError('Create must be new; other operations must target existing rules')
        if not set(card['evidence'])<=set(evidence):raise ValueError('Unknown evidence')
        sources=[evidence[e] for e in card['evidence']]
        if card['scope']=='general' and len({s['case_id'] for s in sources})<2:raise ValueError('General rule requires multiple periods')
        if action=='create' and not any(s['category']=='missing_rule' for s in sources):raise ValueError('New rule requires missing-rule evidence')
        if action in {'correct','reinforce'} and not any(rid in s['rule_ids'] for s in sources):raise ValueError('Update must attribute target rule')
        if action=='merge':
            remove=op.get('remove',[])
            if not remove or rid in remove or not set(remove)<=set(pool):raise ValueError('Invalid merge sources')
            for old in remove:del pool[old]
        pool[rid]=card
    if len(pool)>100:raise ValueError('Experience budget exceeded; merge or narrow rules')
    return sorted(pool.values(),key=lambda c:c['id'])
