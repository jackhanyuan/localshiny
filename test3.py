from connectDB import get_db
import gc

db, cur = get_db()

# delete user
# for i in ['admin_不知道', 'test3', 'haha']:
#     cur.execute("DELETE FROM user where username = ? ", [i])
# x = cur.execute("SELECT * FROM user ")
# print(x.fetchall())

# delete app
# cur.execute("DELETE FROM app where  app_author = ?",['admin'])
# x = cur.execute("SELECT * FROM app ")
# print(x.fetchall())

db.commit()
cur.close()
db.close()
gc.collect()

# print(app_summary)
# print(n)

