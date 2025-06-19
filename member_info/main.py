from member_info  import get_amount, get_cardid

name = 
result = get_cardid.get_person_info(name)

for member in result:
    id = member.get('certId')
    amount = get_amount.get_total_amount(id)
