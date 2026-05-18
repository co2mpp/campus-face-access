"""
批量注册人脸照片
图片命名格式: 学号_姓名.jpg（如 20230001_张三.jpg）
用法: python batch_register.py
自动扫描 人脸图片/ 文件夹下的所有图片并注册
"""
import sys
import os
import re
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from server.config import SERVER_PORT

SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"

# 文件名格式: 学号_姓名.扩展名
FILENAME_PATTERN = re.compile(r'^(\d+)_(.+)')


def parse_filename(filepath):
    """从文件名解析学号和姓名，返回 (stu_no, name) 或 None"""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    m = FILENAME_PATTERN.match(basename)
    if not m:
        return None
    return m.group(1), m.group(2)


def get_student_by_stuno(stu_no):
    resp = requests.get(f"{SERVER_URL}/api/student", params={'keyword': stu_no})
    if resp.status_code == 200:
        data = resp.json()
        if data['total'] > 0:
            return data['data'][0]
    return None


def register_student(stu_no, name, department="智能科学与技术"):
    resp = requests.post(
        f"{SERVER_URL}/api/student",
        json={"stu_no": stu_no, "name": name, "department": department}
    )
    if resp.status_code == 201:
        return resp.json()['id']
    elif resp.status_code == 409:
        # 已存在，查询ID
        existing = get_student_by_stuno(stu_no)
        if existing:
            return existing['id']
    print(f"  创建学生失败 ({stu_no} {name}): {resp.text}")
    return None


def has_face(student_id):
    resp = requests.get(f"{SERVER_URL}/api/face/student/{student_id}")
    return resp.status_code == 200


def register_face(student_id, photo_path):
    with open(photo_path, 'rb') as f:
        filename = os.path.basename(photo_path)
        files = {'photo': (filename, f, 'image/jpeg')}
        resp = requests.post(
            f"{SERVER_URL}/api/face/register",
            data={'student_id': str(student_id)},
            files=files
        )
    if resp.status_code == 200:
        return resp.json()
    print(f"  注册人脸失败: {resp.text}")
    return None


def main():
    face_dir = os.path.join(os.path.dirname(__file__), '人脸图片')
    if not os.path.isdir(face_dir):
        print(f"人脸图片目录不存在: {face_dir}")
        sys.exit(1)

    images = []
    for ext in ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG'):
        images.extend(glob.glob(os.path.join(face_dir, ext)))

    if not images:
        print("未找到任何图片文件")
        sys.exit(1)

    print(f"找到 {len(images)} 张照片")
    print("=" * 60)

    success = 0
    skipped = 0
    failed = 0

    for idx, img_path in enumerate(images, start=1):
        basename = os.path.basename(img_path)
        parsed = parse_filename(img_path)
        if not parsed:
            print(f"[{idx}/{len(images)}] ⚠ 跳过: {basename}（文件名格式不正确，应为 学号_姓名.扩展名）")
            skipped += 1
            continue

        stu_no, name = parsed
        print(f"[{idx}/{len(images)}] {name} ({stu_no}) ← {basename}")

        # 检查学生是否已存在
        existing_student = get_student_by_stuno(stu_no)
        if existing_student:
            print(f"  学生已存在 (ID={existing_student['id']})，跳过创建")
            student_id = existing_student['id']
            # 检查是否已注册人脸
            if has_face(student_id):
                print(f"  人脸已注册，跳过")
                skipped += 1
                continue
        else:
            student_id = register_student(stu_no, name)
            if not student_id:
                failed += 1
                continue

        result = register_face(student_id, img_path)
        if result:
            print(f"  ✅ 注册成功! 版本号: {result.get('feature_version')}")
            success += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"完成: {success} 成功, {skipped} 跳过, {failed} 失败 (共 {len(images)} 张)")
    print(f"管理后台: http://127.0.0.1:{SERVER_PORT}/admin")


if __name__ == '__main__':
    main()
