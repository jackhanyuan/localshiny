import time
import base64
import hmac


# 生成token
def generate_token(username, expire=3600):
	time_str = str(time.time() + expire)
	time_byte = time_str.encode("utf-8")
	sha1_user_str = hmac.new(username.encode("utf-8"), time_byte, 'sha1').hexdigest()
	token = time_str + ':' + sha1_user_str
	b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
	# print(b64_token.decode("utf-8"))
	return b64_token.decode("utf-8")


# 验证token
def certify_token(username, token):
	try:
		token_str = base64.urlsafe_b64decode(token).decode('utf-8')
		token_list = token_str.split(':')
		if len(token_list) != 2:
			return False
		time_str = token_list[0]
		if float(time_str) < time.time():
			# token expired
			return False
		known_sha1_user_str = token_list[1]
		cal_sha1_user_str = hmac.new(username.encode("utf-8"), time_str.encode('utf-8'), 'sha1').hexdigest()
		if known_sha1_user_str != cal_sha1_user_str:
			# token certification failed
			return False
		# token certification success
		return True
	except:
		return False


# print(generate_token("admin"))
#
print(certify_token("python", 'MTYxNDEzODY4Ny4wNDU2NTU1Ojg1OGEyMDg4MzIzYzZkYjVlNWE2ZDhkNTNjM2EyODI3NDEwNDhhMTk='))