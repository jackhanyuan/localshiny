from flask import Flask, render_template, request, session, redirect


@app.route('/api/v1/admin/register',methods=['POST'])
def register():
	username = request.form.get('username')
	password = request.form.get('password')
	save = Shop_list(userName=username)
	save.hash_password(password) #调用密码加密方法
	db.session.add(save)
	db.session.commit()
	return 'success'


@app.route('/api/v1/admin/login',methods=['POST'])
def login():
	username = request.form.get('username')
	password = request.form.get('password')
	obj = Shop_list.query.filter_by(userName=username).first()
	if not obj:
		return res_json(201,'','未找到该用户')
	if obj.verify_password(password):
		token = generate_token(username)
		return res_json(200,{'token':token},'登录成功')
	else:
		return res_json(201,'','密码错误')



