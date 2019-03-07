from wxpy import *
import re
import json
import unicodedata
import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
   

bot = Bot(console_qr = 2)
bot.enable_puid()

tuling = Tuling(api_key='fec1dbaad9ea4c6b8799069c163c63e1')

transport = RequestsHTTPTransport("https://sai-mainnet.makerfoundation.com/v1")
client = Client(transport=transport)

admin_group = bot.groups().search('重要意见群')
member_fouls = defaultdict(int)

@bot.register(admin_group, except_self = True)

def detect_msg(msg):
	current_group = msg.chat
	print (current_group)
	print (msg.text)
	title = msg.text
	url = msg.url
	if len(url) > 0:
		print ('detect articles....')
		print (msg.member.nick_name)
		if re.search('Maker',msg.member.nick_name,re.IGNORECASE):
			pass
		else:
			raw_content = requests.get(url).text
			content = re.sub('@[^\s]*', '', unicodedata.normalize('NFKC', raw_content)).strip()
			print(content)
			if (not re.search('Maker|MakerDAO|稳定币|加密经济|潘超|Dai|开发者',title, re.IGNORECASE)) \
			and (not re.search('Maker|MakerDAO|稳定币|加密经济|潘超|央行|Ethfans',content, re.IGNORECASE)):
				print (member_fouls)
				member_fouls[msg.member] += 1
				print (member_fouls)
				if member_fouls[msg.member] == 1:
				  msg.reply('@{} 嘀嘀嘀，我是 MakerAI。监测出你在发无关的内容。先给一张黄牌哦, [微笑]'.format(msg.member.nick_name))
				  msg.reply('如果我判断错了，请@我并告诉我一声“是篇好文章”')
				  member_fouls[msg.member] += 1
				elif member_fouls[msg.member] > 1:
				  msg.reply('@{} 你已经两次发无关内容，只好请你出群了。[再见]'.format(msg.member.nick_name))
				  current_group.remove_members(msg.member)
				  member_fouls.pop(msg.member,None)
	if re.search('错了|不好意思|对不起', msg.text, re.IGNORECASE) and (msg.member in member_fouls.keys()) and member_fouls[msg.member] > 0:
		msg.reply('知错就改还是好孩子！')
	if re.search('好文章', msg.text, re.IGNORECASE) and (msg.member in member_fouls.keys()) and member_fouls[msg.member] > 0 and msg.is_at:
		member_fouls[msg.member] = 0
		msg.reply('好，那是我错怪你了，[愉快]')
		print (member_fouls)

	if msg.is_at:
		text = msg.text
		pattern = r"cdp(:|\s+)?(?P<id>\d*)"
		match = re.search(pattern, text,re.IGNORECASE)
		if re.search('好文章', text, re.IGNORECASE) and (msg.member in member_fouls.keys()) and member_fouls[msg.member] > 0:
			member_fouls[msg.member] = 0
			msg.reply('好，那是我错怪你了，[愉快]')
			print (member_fouls)
		elif match:
			cdp_id = match.group('id')
			query = gql('''
			{
			  getCup(id: %s){
			  	pip
			    id
			    art
			    ratio
			  }
			}
			''' % (cdp_id))
			variables = {'cdp_id': cdp_id}
			result = client.execute(query)['getCup']
			if result:
				this_id = result['id']
				amount = round(float(result['art']),2)
				ratio = round(float(result["ratio"]),2) if result["ratio"] != None else 0
				li_price = None if ratio == 0 else round(float(result['pip'])/(ratio/150),2)
				spot_price = float(result['pip'])
				if 0 < ratio <  160:
					status = "危险 [惊恐]"
				elif 160 <= ratio < 180:
					status = "风险 [发呆]"
				elif ratio >= 180:
					status = "安全 [得意]"
				else:
					status = "没有债务"
				cdp_response = "CDP:{id}\n状态:{status}\nDai款:{amt}\n清算价格:{li_price}\n实时价格:{spot_price}\n抵押率:{ratio}%".format(id=this_id, status=status,amt=amount,li_price=li_price,spot_price=spot_price,ratio=ratio)
				msg.reply(cdp_response)
		else:
			tuling.do_reply(msg)
                
embed()
