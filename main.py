from fastapi import FastAPI, Request, HTTPException
import mysql.connector
import logging
import os
from logging.handlers import RotatingFileHandler
### FastAPI 애플리케이션 객체 생성 (API 서버의 시작점)
app = FastAPI()

### DB 연결을 생성하는 함수 (요청마다 MySQL과 연결)
def get_db():
  return mysql.connector.connect(
      host="localhost",
      port=3306,
      user="root",
      password="1234",
      database="test_db"
  )

## Logging ##

os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

formatter = logging.Formatter(LOG_FORMAT)

file_handler = RotatingFileHandler(
    filename="logs/app.log",
    maxBytes= 1024,  # 5MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logging.getLogger("uvicorn").handlers = root_logger.handlers
logging.getLogger("uvicorn.access").handlers = root_logger.handlers
logging.getLogger("uvicorn.error").handlers = root_logger.handlers

# ---------------------------
# CREATE
# ---------------------------
@app.post("/todos")
async def create_todo(request: Request):
  ### 요청 body(JSON) 파싱
  body = await request.json()
  content = body.get("content")



  ### 필수 값 검증 (content 없으면 에러 반환)
  if not content:
      raise HTTPException(status_code=400, detail="content is required")



  ### DB 연결 및 SQL 실행 준비
  conn = get_db()
  cursor = conn.cursor()



  # INSERT
  # insert into ~ values ~ 절을 활용하여 todoList row를 삽입합니다.
  # insert into todo : todo 테이블에 새로운 데이터를 삽입하겠다는 의미
  # (content) values (%s) content 컬럼에 values 다음에 올 값을 넣겠다는 의미
  # , (content,) content string값을 %s 자리에 대입한다는 의미
  cursor.execute(
      "INSERT INTO todo (content) VALUES (%s)",
      (content,)
  )



  ### INSERT 결과를 DB에 실제 반영
  conn.commit()



  ### 방금 생성된 row의 PK(id) 값 가져오기
  todo_id = cursor.lastrowid



  # SELECT (방금 생성한 todo 조회)
  # select ~ from ~ where 절을 이용하여 방금 삽입한 todo 를 불러옵니다.
  # SELECT id, content, created_at : id,content,create_at값을 불러오겠다는 의미
  # FROM todo : todo 테이블에서 값을 불러오겠다는 의미
  # WHERE id = %s : id가 %s인값을 불러오겠다는 의미
  # , (todo_id,) : %s에 todo_id값을 대입하겠다는 의미
  cursor.execute(
      "SELECT id, content, created_at FROM todo WHERE id = %s",
      (todo_id,)
  )
  row = cursor.fetchone()



  ### DB 연결 종료
  cursor.close()
  conn.close()



  ### 생성된 todo 데이터를 JSON 형태로 반환
  return {
      "id": row[0],
      "content": row[1],
      "created_at": str(row[2])
  }


# ---------------------------
# READ
# ---------------------------
@app.get("/todos")
def get_todos():
  ### DB 연결
  conn = get_db()
  cursor = conn.cursor()



 # 전체 조회
 # select ~ from ~ order by ~ 를 활용하여 전체 todo list를 만든 최근에 만든 순으로 조회합니다.
 # SELECT id, content, created_at : id,content,create_at값을 불러오겠다는 의미
 # FROM todo : todo 테이블에서 값을 불러오겠다는 의미
 # ORDER BY id DESC  id값 기준 내림차순으로 정렬하겠다는 의미
  cursor.execute(
      "SELECT id, content, created_at FROM todo ORDER BY id DESC"
  )
  rows = cursor.fetchall()



  ### DB 연결 종료
  cursor.close()
  conn.close()



  ### 여러 개의 row를 JSON 리스트 형태로 변환하여 반환
  return [
      {
          "id": r[0],
          "content": r[1],
          "created_at": str(r[2])
      }
      for r in rows
  ]


# ---------------------------
# DELETE
# ---------------------------
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
  ### URL 경로 변수(todo_id)로 삭제 대상 지정
  conn = get_db()
  cursor = conn.cursor()



  # DELETE
  # delete from ~ where ~ 절을 활용하여 todo list를 삭제합니다.
  # delete from todo : todo 테이블에서 값을 삭제하겠다는 의미
  # WHERE id = %s : id가 %s인값을 삭제하겠다는 의미
  # , (todo_id,) : %s에 todo_id값을 대입하겠다는 의미
  cursor.execute(
      "DELETE FROM todo WHERE id = %s",
      (todo_id,)
  )



  ### 삭제 결과 DB 반영
  conn.commit()



  ### 실제로 삭제된 행의 개수
  affected = cursor.rowcount



  ### DB 연결 종료
  cursor.close()
  conn.close()



  ### 삭제 대상이 없었을 경우 404 반환
  if affected == 0:
      raise HTTPException(status_code=404, detail="Todo not found")



  ### 삭제 성공 메시지 반환
  return {"message": "Todo deleted"}


