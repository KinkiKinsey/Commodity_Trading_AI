from bs4 import BeautifulSoup
import time
import os
import json
from datetime import datetime
import logging
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db_config import DB_CONFIG
from time import sleep

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('sina_news_crawler')

class SinaNewsCrawler:
    def __init__(self):
        self.url = "https://finance.sina.com.cn/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data_dir = "data"
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        # 初始化数据库连接
        self.init_db()

        # 记录上次保存的新闻时间
        self.last_save_time = None

    def get_page_content(self):
        """使用Selenium模拟浏览器获取页面内容"""
        driver = None
        try:
            # 配置Chrome浏览器选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
            chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
            chrome_options.add_argument('--no-sandbox')  # 禁用沙盒模式
            chrome_options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')  # 设置User-Agent
            
            # 初始化Chrome浏览器
            logger.info("初始化Chrome浏览器")
            chrome_driver_path =  r'C:\Users\wangruilin\.cache\selenium\chromedriver\win64\134.0.6998.165\chromedriver.exe'  # 请确认你的ChromeDriver路径
            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置页面加载超时时间
            driver.set_page_load_timeout(30)
            
            # 访问目标网页
            logger.info(f"使用Selenium访问页面: {self.url}")
            driver.get(self.url)
            
            # 等待页面加载完成（等待body元素可见）
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待一段时间，确保JavaScript动态内容加载完成
            logger.info("等待页面动态内容加载...")
            time.sleep(3)
            
            # 获取页面源码
            html_content = driver.page_source
            logger.info(f"成功获取页面内容，内容长度: {len(html_content)}字节")
            
            return html_content
        except Exception as e:
            logger.error(f"Selenium请求异常: {str(e)}")
            return None
        finally:
            # 确保浏览器关闭
            if driver:
                driver.quit()
                logger.info("已关闭Chrome浏览器")

    def parse_news(self, html_content):
        """解析新闻内容"""
        if not html_content:
            logger.error("没有获取到HTML内容")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 保存HTML到文件以便检查
        try:
            with open("sina_finance_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("已保存页面HTML到sina_finance_page.html文件")
        except Exception as e:
            logger.error(f"保存HTML文件时出错: {str(e)}")
        
        news_items = []
        
        # 5. 尝试查找动态加载的新闻元素
        bd_i_elements = soup.find_all("div", class_="bd_i")
        if bd_i_elements:
            logger.info(f"找到{len(bd_i_elements)}个bd_i新闻元素")
            for news in bd_i_elements:
                try:
                    content_elem = news.find("span", class_="bd_i_txt")
                    content = content_elem.text.strip() if content_elem else ""
                    
                    # 提取标题，优先从 content 中提取【】里的内容，否则生成默认标题
                    title = ""
                    if "【" in content and "】" in content:
                        title = content.split("【")[1].split("】")[0]  # 提取第一个【】中的内容
                    else:
                        # 如果没有【】内容，则取 content 的第一句话作为标题
                        title = content.split("。")[0] if content else "短讯标题"  # 获取第一句话
                    
                    # 限制标题长度：第一句话超过100个汉字或300个字符时，截取到第一个标点符号的位置
                    if len(title) > 100 or len(title) > 300:
                        for punct in [";", "!", "？", "!", "?", "//"]:
                            title = title.split(punct)[0]
                            if title:
                                break

                    news_items.append({
                        'title': title,
                        'content': content,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    logger.info(f"提取到动态新闻: {content}")
                except Exception as e:
                    logger.error(f"解析bd_i新闻元素时出错: {str(e)}")
        
        if not news_items:
            logger.warning("未能找到任何新闻内容")
        else:
            logger.info(f"共找到{len(news_items)}条新闻")
        
        return news_items[:10]  # 只返回前10条新闻

    def init_db(self):
        """初始化数据库连接并创建表"""
        try:
            # 连接到MySQL数据库
            self.conn = pymysql.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset=DB_CONFIG['charset']
            )
            self.cursor = self.conn.cursor()
            
            # 连接到指定数据库
            self.cursor.execute(f"USE {DB_CONFIG['database']}")
            
            # 创建新闻表 t_news（如果不存在）
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS t_news (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
                news_type_id BIGINT DEFAULT NULL COMMENT '新闻类型ID（字典ID，已废弃）',
                news_type_name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '新闻类型名称',
                title VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '新闻标题',
                img_url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标题图片URL',
                label VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标签（VIP，外交，会谈等）',
                author VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '作者（新闻出处）',
                content LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '新闻内容',
                pv INT DEFAULT '1' COMMENT '页面浏览量',
                is_delete TINYINT DEFAULT '0' COMMENT '是否删除： 0否 1是，默认0',
                create_date DATETIME DEFAULT NULL COMMENT '创建时间',
                create_by VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建人',
                update_date DATETIME DEFAULT NULL COMMENT '更新时间',
                update_by VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '更新人'
            ) ENGINE=InnoDB AUTO_INCREMENT=355 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='资讯表';
            """)
            
            self.conn.commit()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            self.conn = None
            self.cursor = None

    def save_to_db(self, news_items):
        """保存新闻数据到MySQL数据库"""
        if not news_items or not self.conn:
            return

        try:
            # 获取当前日期，作为标题的一部分
            current_date = datetime.now().strftime('%Y-%m-%d')

            # 准备SQL语句
            sql = """
                INSERT INTO t_news (news_type_id, news_type_name, title, img_url, label, author, content, pv, is_delete, create_date, create_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 准备数据，确保数据字段与表字段对应
            values = []
            for idx, item in enumerate(news_items):
                title = item['title']
                content = item['content']

                # 生成唯一的 news_type_id，设置为 NULL
                news_type_id = None  # news_type_id 设置为 NULL
                
                # 过滤掉已存在的新闻，避免重复插入

                self.cursor.execute("SELECT COUNT(*) FROM t_news WHERE content = %s", (content,))
                result = self.cursor.fetchone()
                if result[0] > 0:
                    logger.info(f"跳过重复新闻: {title}")
                    continue  # 跳过重复的新闻

                # 获取当前新闻的发布时间
                crawl_time = datetime.now()

                # 检查新闻发布时间是否比上一个新闻慢1秒
                if self.last_save_time:
                    time_difference = (crawl_time - self.last_save_time).total_seconds()
                    if time_difference < 1:
                        logger.info("等待1秒，确保新闻发布时间间隔大于1秒")
                        sleep(1)
                        crawl_time = datetime.now()  # 再次获取更新时间

                # 更新上次保存的新闻时间
                self.last_save_time = crawl_time

                # 填充数据库字段
                values.append((
                    news_type_id,               # news_type_id
                    "短讯",                      # news_type_name
                    title,                       # title
                    None,                        # img_url为空
                    "短讯",                      # label
                    "新浪财经",                 # author
                    content,                     # content
                    1,                           # pv，默认设为1
                    0,                           # is_delete，默认设为0
                    crawl_time,                 # create_date，当前时间
                    "admin"                      # create_by，设置为admin
                ))

            # 执行批量插入
            self.cursor.executemany(sql, values)
            self.conn.commit()

            logger.info(f"成功保存{len(news_items)}条新闻到数据库")
        except Exception as e:
            logger.error(f"保存新闻到数据库时出错: {str(e)}")
            self.conn.rollback()

    def save_news(self, news_items):
        """保存新闻数据到JSON文件和数据库"""
        if not news_items:
            logger.info("没有新闻数据需要保存")
            return
        
        # 保存到JSON文件
        filename = os.path.join(self.data_dir, f"sina_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存{len(news_items)}条新闻到{filename}")
        except Exception as e:
            logger.error(f"保存新闻数据到JSON文件时出错: {str(e)}")
        
        # 保存到数据库
        self.save_to_db(news_items)

    def run(self):
        """运行爬虫"""
        logger.info("开始爬取新浪财经新闻")
        html_content = self.get_page_content()
        news_items = self.parse_news(html_content)
        self.save_news(news_items)
        logger.info("爬取完成")
        
        # 关闭数据库连接
        if self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("数据库连接已关闭")

# 主函数
def main():
    crawler = SinaNewsCrawler()
    crawler.run()

if __name__ == "__main__":
    main()