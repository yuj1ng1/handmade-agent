import os
import json
from logger_config import logger

class MemoryStore:
    def __init__(self,memory_path):
        self.memory_path=memory_path

    def save(self,user_memory,conversation_summary):
        memory_data={
            "user_memory":user_memory,
            "conversation_summary":conversation_summary
        }

        #创建临时路径
        temp_path=self.memory_path.with_name(
            self.memory_path.name+".tmp"
        )

        with open(temp_path,"w",encoding="utf-8")as f:
            json.dump(
                memory_data,
                f,
                ensure_ascii=False,
                indent=4
            )
        os.replace(
            temp_path,
            self.memory_path
        )

    def load_memory(self):
        try:
            with open(self.memory_path,"r",encoding="utf-8")as f:
                return json.load(f)

        except FileNotFoundError:
            logger.info("memory.json文件不存在使用空记忆")
        except json.JSONDecodeError as e:
            logger.error(
                f"memory.json解析失败 "
                f"error={e}"
            )
            try:
                self.backup_badmemory()
            except OSError as backup_error:
                logger.error(
                    f"损坏的memory.json文件备份失败"
                    f"error={backup_error}"
                )
        except OSError as e:
            logger.error(
                f"memory.json读取失败"
                f"error={e}"
            )
        return {}
        
    def backup_badmemory(self):
        bad_path=self.memory_path.with_name(
            self.memory_path.name+".bad"
        )

        os.replace(
            self.memory_path,
            bad_path
        )
        logger.info(
            f"损坏的memory.json文件已备份"
            f"path={bad_path}"
        )