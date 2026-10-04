"""Pure before/after comparisons for workshop results; never mutate items."""

def changes(before, after):
    result=[]
    for side in ('prefixes','suffixes'):
        old={a['stat']:a for a in before.get(side,[])}
        new={a['stat']:a for a in after.get(side,[])}
        for stat in sorted(set(old)|set(new)):
            a,b=old.get(stat),new.get(stat)
            if a==b: continue
            if a is not None and b is not None and all(a.get(field)==b.get(field) for field in ('val','tier','fractured','crafted')):
                continue
            kind='added' if a is None else 'removed' if b is None else 'changed'
            result.append(dict(kind=kind,side=side,stat=stat,before=a,after=b))
    for stat in sorted(set(before.get('itemBase',{}))|set(after.get('itemBase',{}))):
        a,b=before.get('itemBase',{}).get(stat),after.get('itemBase',{}).get(stat)
        if a!=b: result.append(dict(kind='changed',side='base',stat=stat,before={'val':a},after={'val':b}))
    for field in ('rarity','is_corrupted'):
        a,b=before.get(field,False),after.get(field,False)
        if a!=b: result.append(dict(kind='changed',side='item',stat=field,before=a,after=b))
    return result
