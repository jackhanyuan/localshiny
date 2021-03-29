import time
import base64
import hmac
import uuid
import hashlib


# token生成
def generate_token(username, expire=3600 * 24 * 7):
	time_str = str(time.time() + expire)
	time_byte = time_str.encode("utf-8")
	sha1_user_str = hmac.new(username.encode("utf-8"), time_byte, 'sha1').hexdigest()
	token = time_str + '-' + sha1_user_str + '-' + username
	b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))
	# print(b64_token.decode("utf-8"))
	return b64_token.decode("utf-8")


# 从token中解析username和time_str
def get_username_time_from_token(token):
	token_str = base64.urlsafe_b64decode(token).decode('utf-8')
	token_list = token_str.split('-')
	if len(token_list) != 3:
		return False
	time_str = token_list[0]
	username = token_list[2]
	return username, time_str


# 8位id生成
array = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
def generate_short_id():
	uid = str(uuid.uuid4()).replace("-", '')  # 注意这里需要用uuid4
	buffer = []
	for i in range(0, 8):
		start = i * 4
		end = i * 4 + 4
		val = int(uid[start:end], 16)
		buffer.append(array[val % 62])
	return "".join(buffer)


# if __name__ == '__main__':
#     print(generate_token('test_name'))
#     print(generate_short_id())
