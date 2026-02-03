# backend/models/mysql_db.py
"""
MySQL 연결 관리 (member 테이블)
"""
import pymysql
from contextlib import contextmanager
from app.config import settings


def get_mysql_connection():
    """MySQL 커넥션 생성"""
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def mysql_cursor():
    """MySQL 커서 컨텍스트 매니저"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def upsert_member(profile: dict) -> dict:
    """
    네이버 프로필 기반 회원 upsert.
    - 신규: INSERT + to_cnt=1
    - 기존: to_cnt += 1, last_visit 갱신
    반환: member row (dict)
    """
    with mysql_cursor() as cur:
        # 기존 회원 조회 (naver_id 기준)
        cur.execute("SELECT * FROM member WHERE naver_id = %s", (profile["naver_id"],))
        row = cur.fetchone()

        if row:
            # 기존 회원 → 방문 수 증가 + last_visit 갱신
            cur.execute(
                """
                UPDATE member
                SET to_cnt     = to_cnt + 1,
                    last_visit  = NOW(),
                    name        = %s,
                    nickname    = %s,
                    mem_photo   = %s,
                    gender      = %s,
                    birthday    = %s,
                    age         = %s,
                    birth_year  = %s
                WHERE naver_id = %s
                """,
                (
                    profile["name"],
                    profile["nickname"],
                    profile["mem_photo"],
                    profile["gender"],
                    profile["birthday"],
                    profile["age"],
                    profile["birth_year"],
                    profile["naver_id"],
                ),
            )
            # 갱신된 row 다시 조회
            cur.execute("SELECT * FROM member WHERE naver_id = %s", (profile["naver_id"],))
            row = cur.fetchone()
        else:
            # 신규 회원
            cur.execute(
                """
                INSERT INTO member
                    (naver_id, email, name, nickname, mem_photo, gender, birthday, age, birth_year, to_cnt)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    profile["naver_id"],
                    profile["email"],
                    profile["name"],
                    profile["nickname"],
                    profile["mem_photo"],
                    profile["gender"],
                    profile["birthday"],
                    profile["age"],
                    profile["birth_year"],
                ),
            )
            cur.execute("SELECT * FROM member WHERE naver_id = %s", (profile["naver_id"],))
            row = cur.fetchone()

    # datetime → str 직렬화
    for key in ("frst_visit", "last_visit"):
        if row.get(key):
            row[key] = row[key].isoformat()

    return row
