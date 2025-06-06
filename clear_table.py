#!/usr/bin/env python3
"""
SQLite表清空脚本
用法: python clear_table.py <数据库文件> <表名1> [表名2] [表名3] ...
"""

import logging
import os
import sqlite3
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def clear_single_table(
    cursor: sqlite3.Cursor, table_name: str
) -> tuple[bool, int]:
    """
    清空单个表的内容

    Args:
        cursor: 数据库游标
        table_name: 要清空的表名

    Returns:
        Tuple[bool, int]: (操作是否成功, 删除的记录数)
    """
    try:
        # 检查表是否存在
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            print(f"错误: 表 '{table_name}' 不存在")
            return False, 0

        # 获取清空前的记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]

        if record_count == 0:
            print(f"表 '{table_name}' 已经是空的")
            return True, 0

        # 清空表内容
        cursor.execute(f"DELETE FROM {table_name}")

        # 重置自增ID (如果表有自增主键)
        try:
            cursor.execute(
                f"DELETE FROM sqlite_sequence WHERE name='{table_name}'"
            )
        except sqlite3.Error:
            # 如果没有自增字段，忽略错误
            pass

        print(f"成功: 表 '{table_name}' 已清空，删除了 {record_count} 条记录")
        return True, record_count

    except sqlite3.Error:
        logger.exception(f"清空表 '{table_name}' 时发生SQLite错误")
        return False, 0
    except Exception:
        logger.exception(f"清空表 '{table_name}' 时发生未知错误")
        return False, 0


def clear_tables(
    db_path: str, table_names: list[str], confirm_each: bool = True
) -> bool:
    """
    清空指定SQLite表的内容

    Args:
        db_path: 数据库文件路径
        table_names: 要清空的表名列表
        confirm_each: 是否对每个表单独确认

    Returns:
        bool: 操作是否完全成功
    """
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件 '{db_path}' 不存在")
            return False

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 验证所有表是否存在
        existing_tables = []
        missing_tables = []

        for table_name in table_names:
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """,
                (table_name,),
            )

            if cursor.fetchone():
                existing_tables.append(table_name)
            else:
                missing_tables.append(table_name)

        if missing_tables:
            print(f"错误: 以下表不存在: {', '.join(missing_tables)}")
            if not existing_tables:
                conn.close()
                return False
            print(f"将继续处理存在的表: {', '.join(existing_tables)}")

        # 显示要清空的表的统计信息
        total_records = 0
        table_stats = []

        for table_name in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            table_stats.append((table_name, count))

        print(f"\n即将清空 {len(existing_tables)} 个表:")
        for table_name, count in table_stats:
            print(f"  - {table_name}: {count} 条记录")
        print(f"总计: {total_records} 条记录")

        if total_records == 0:
            print("所有表都已经是空的")
            conn.close()
            return True

        # 确认操作
        if confirm_each:
            confirm = input(
                f"\n确定要清空这 {len(existing_tables)} 个表吗？(y/N): "
            )
            if confirm.lower() not in ["y", "yes", "是"]:
                print("操作已取消")
                conn.close()
                return False

        # 逐个清空表
        successful_tables = []
        failed_tables = []
        total_deleted = 0

        print("\n开始清空表...")
        for table_name in existing_tables:
            success, deleted_count = clear_single_table(cursor, table_name)
            if success:
                successful_tables.append(table_name)
                total_deleted += deleted_count
            else:
                failed_tables.append(table_name)

        # 提交更改
        conn.commit()
        conn.close()

        # 汇总结果
        print("\n操作完成:")
        print(
            f"成功清空: {len(successful_tables)} 个表 ({total_deleted} 条记录)"
        )
        if failed_tables:
            print(
                f"清空失败: {len(failed_tables)} 个表 ({', '.join(failed_tables)})"
            )

        return len(failed_tables) == 0

    except sqlite3.Error:
        logger.exception("SQLite错误")
        return False
    except Exception:
        logger.exception("未知错误")
        return False


def clear_tables_force(db_path: str, table_names: list[str]) -> bool:
    """
    强制清空指定表（无需确认）

    Args:
        db_path: 数据库文件路径
        table_names: 要清空的表名列表

    Returns:
        bool: 操作是否完全成功
    """
    return clear_tables(db_path, table_names, confirm_each=False)


def list_tables(db_path: str):
    """
    列出数据库中的所有表

    Args:
        db_path: 数据库文件路径
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        )

        tables = cursor.fetchall()

        if tables:
            print("数据库中的表:")
            total_records = 0
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"  - {table[0]} ({count} 条记录)")
            print(f"\n总计: {len(tables)} 个表，{total_records} 条记录")
        else:
            print("数据库中没有用户表")

        conn.close()

    except sqlite3.Error:
        logger.exception("SQLite错误")
    except Exception:
        logger.exception("未知错误")


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        print(__doc__)
        print("\n可选参数:")
        print("  -h, --help     显示此帮助信息")
        print("  -l, --list     列出数据库中的所有表")
        print("  -f, --force    强制清空（无需确认）")
        print("\n示例:")
        print("  python clear_table.py app.db users")
        print("  python clear_table.py app.db users posts comments")
        print("  python clear_table.py -f app.db users posts")
        print("  python clear_table.py -l app.db")
        return

    if len(sys.argv) == 3 and sys.argv[1] in ["-l", "--list"]:
        db_path = sys.argv[2]
        list_tables(db_path)
        return

    if len(sys.argv) < 3:
        print(
            "用法: python clear_table.py <数据库文件> <表名1> [表名2] [表名3] ..."
        )
        print("使用 -h 查看帮助信息")
        sys.exit(1)

    # 检查是否为强制模式
    force_mode = False
    start_idx = 1

    if sys.argv[1] in ["-f", "--force"]:
        force_mode = True
        start_idx = 2
        if len(sys.argv) < 4:
            print(
                "用法: python clear_table.py -f <数据库文件> <表名1> [表名2] ..."
            )
            sys.exit(1)

    db_path = sys.argv[start_idx]
    table_names = sys.argv[start_idx + 1 :]

    # 执行清空操作
    if force_mode:
        success = clear_tables_force(db_path, table_names)
    else:
        success = clear_tables(db_path, table_names)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
