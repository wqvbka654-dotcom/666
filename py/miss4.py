# -*- coding: utf-8 -*-
from base.spider import Spider
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urlparse
import time

class Spider(Spider):
    def __init__(self):
        super().__init__()
        
    def getName(self):
        return "MissAV2"
        
    def init(self, extend):
        # 域名列表，按优先级排序
        self.domains = [
            "https://www.missav2.one",
            "https://www.missav365.cc", 
            "https://www.missav365.icu", 
            "https://www.missav365.top"
        ]
        self.current_domain_index = 0
        self.base_url = self.domains[self.current_domain_index]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.base_url + '/',
        })
        
        # 测试域名可用性（可选）
        # self._test_domains()

    def _test_domains(self):
        """测试域名可用性"""
        available_domains = []
        print("正在测试域名可用性...")
        for domain in self.domains:
            try:
                response = requests.head(domain, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    available_domains.append(domain)
                    print(f"✓ 域名可用: {domain}")
                else:
                    print(f"✗ 域名返回错误: {domain} ({response.status_code})")
            except Exception as e:
                print(f"✗ 域名不可用: {domain} ({str(e)})")
        
        if available_domains:
            self.domains = available_domains
            self.base_url = self.domains[0]
            print(f"使用域名: {self.base_url}")
        else:
            print("警告：所有域名都不可用，使用默认配置")
        
        return available_domains

    def _switch_domain(self):
        """切换到下一个可用域名"""
        if self.current_domain_index < len(self.domains) - 1:
            self.current_domain_index += 1
        else:
            self.current_domain_index = 0
        
        old_url = self.base_url
        self.base_url = self.domains[self.current_domain_index]
        self.session.headers.update({
            'Referer': self.base_url + '/',
        })
        print(f"域名切换: {old_url} → {self.base_url}")
        return self.base_url

    def _make_request(self, url, max_retries=2, **kwargs):
        """带重试机制的请求方法"""
        original_index = self.current_domain_index
        retries = 0
        
        while retries < max_retries:
            try:
                # 如果是相对路径，加上基础URL
                if not url.startswith('http'):
                    if url.startswith('/'):
                        url_to_request = self.base_url + url
                    else:
                        url_to_request = self.base_url + '/' + url
                else:
                    url_to_request = url
                
                # 更新Referer头
                referer_domain = self.base_url + '/'
                headers = kwargs.get('headers', {})
                headers['Referer'] = referer_domain
                kwargs['headers'] = headers
                
                response = self.session.get(url_to_request, timeout=10, **kwargs)
                response.encoding = 'utf-8'
                
                # 检查响应是否有效
                if response.status_code == 200:
                    return response
                elif response.status_code in [403, 404, 500]:
                    print(f"请求失败: {response.status_code} - {url_to_request}")
                    # 对于这些错误，立即切换域名重试
                    if retries < max_retries - 1:
                        self._switch_domain()
                        retries += 1
                        time.sleep(0.5)
                        continue
                else:
                    print(f"请求异常状态码: {response.status_code} - {url_to_request}")
                    
            except requests.exceptions.Timeout:
                print(f"请求超时: {url_to_request if 'url_to_request' in locals() else url}")
            except requests.exceptions.ConnectionError:
                print(f"连接错误: {url_to_request if 'url_to_request' in locals() else url}")
            except Exception as e:
                print(f"请求异常: {str(e)[:50]}... - {url_to_request if 'url_to_request' in locals() else url}")
            
            # 切换域名并重试
            if retries < max_retries - 1:
                self._switch_domain()
                retries += 1
                time.sleep(0.5)
            else:
                retries += 1
        
        # 如果所有重试都失败，恢复到原始域名并抛出异常
        self.current_domain_index = original_index
        self.base_url = self.domains[self.current_domain_index]
        raise Exception(f"请求失败，已尝试所有域名: {url}")

    def _extract_domain_name(self, url):
        """从URL中提取域名简称"""
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            
            # 提取主要域名部分
            if 'missav2.one' in netloc:
                return '屌'
            elif 'missav365.cc' in netloc:
                return '戳'
            elif 'missav365.icu' in netloc:
                return '插'
            elif 'missav365.top' in netloc:
                return '操'
            elif 'missav2.icu' in netloc:
                return 'v2.icu'
            else:
                # 返回最简短的域名标识
                parts = netloc.split('.')
                if len(parts) >= 2:
                    return f"{parts[-2]}.{parts[-1]}"
                return netloc
        except:
            return self.base_url.split('//')[-1].split('/')[0]

    def homeContent(self, filter):
        categories = [
            {"type_id": "actresses", "type_name": "女优一览"},
            {"type_id": "actresses/ranking", "type_name": "女优排行"},
            {"type_id": "genres", "type_name": "类型"},
            {"type_id": "makers", "type_name": "发行商"},
        ]
        
        actress_filters = [
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "影片数量", "v": "videos"},
                    {"n": "出道时间", "v": "debut"}
                ]
            },
            {
                "key": "height",
                "name": "身高",
                "value": [
                    {"n": "身高", "v": ""},
                    {"n": "131-135cm", "v": "131-135"},
                    {"n": "136-140cm", "v": "136-140"},
                    {"n": "141-145cm", "v": "141-145"},
                    {"n": "146-150cm", "v": "146-150"},
                    {"n": "151-155cm", "v": "151-155"},
                    {"n": "156-160cm", "v": "156-160"},
                    {"n": "161-165cm", "v": "161-165"},
                    {"n": "166-170cm", "v": "166-170"},
                    {"n": "171-175cm", "v": "171-175"},
                    {"n": "176-180cm", "v": "176-180"},
                    {"n": "181-185cm", "v": "181-185"},
                    {"n": "186-190cm", "v": "186-190"}
                ]
            },
            {
                "key": "cup",
                "name": "罩杯",
                "value": [
                    {"n": "罩杯", "v": ""},
                    {"n": "A", "v": "A"},
                    {"n": "B", "v": "B"},
                    {"n": "C", "v": "C"},
                    {"n": "D", "v": "D"},
                    {"n": "E", "v": "E"},
                    {"n": "F", "v": "F"},
                    {"n": "G", "v": "G"},
                    {"n": "H", "v": "H"},
                    {"n": "I", "v": "I"},
                    {"n": "J", "v": "J"},
                    {"n": "K", "v": "K"},
                    {"n": "L", "v": "L"}
                ]
            },
            {
                "key": "age",
                "name": "年龄",
                "value": [
                    {"n": "年龄", "v": ""},
                    {"n": "<20", "v": "0-20"},
                    {"n": "20-30", "v": "20-30"},
                    {"n": "30-40", "v": "30-40"},
                    {"n": "40-50", "v": "40-50"},
                    {"n": "50-60", "v": "50-60"},
                    {"n": "＞60", "v": "60-99"}
                ]
            },
            {
                "key": "debut",
                "name": "出道年份",
                "value": [
                    {"n": "2026", "v": "2026"},
                    {"n": "2025", "v": "2025"},
                    {"n": "2024", "v": "2024"},
                    {"n": "2023", "v": "2023"},
                    {"n": "2022", "v": "2022"},
                    {"n": "2021", "v": "2021"},
                    {"n": "2020", "v": "2020"},
                    {"n": "2019", "v": "2019"},
                    {"n": "2018", "v": "2018"},
                    {"n": "2017", "v": "2017"},
                    {"n": "2016", "v": "2016"},
                    {"n": "2015", "v": "2015"},
                    {"n": "2014", "v": "2014"},
                    {"n": "2013", "v": "2013"},
                    {"n": "2012", "v": "2012"},
                    {"n": "2011", "v": "2011"},
                    {"n": "2010", "v": "2010"},
                    {"n": "2009", "v": "2009"},
                    {"n": "2008", "v": "2008"},
                    {"n": "2007", "v": "2007"},
                    {"n": "2006", "v": "2006"},
                    {"n": "2005", "v": "2005"},
                    {"n": "2004", "v": "2004"},
                    {"n": "2003", "v": "2003"},
                    {"n": "2002", "v": "2002"},
                    {"n": "2001", "v": "2001"},
                    {"n": "2000", "v": "2000"}            
                ]
            },
            {
                "key": "filters",
                "name": "视频过滤",
                "value": [
                    {"n": "所有", "v": ""},
                    {"n": "单人作品", "v": "individual"},
                    {"n": "多人作品", "v": "multiple"},
                    {"n": "中文字幕", "v": "chinese-subtitle"},
                ]
            },
            {
                "key": "sort",
                "name": "视频排序",
                "value": [
                    {"n": "默认", "v": ""},
                    {"n": "发行日期", "v": "released_at"},
                    {"n": "最近更新", "v": "published_at"},
                    {"n": "收藏数", "v": "saved"},
                    {"n": "今日浏览", "v": "today_views"},
                    {"n": "本周浏览", "v": "weekly_views"},
                    {"n": "本月浏览", "v": "monthly_views"},
                    {"n": "总浏览", "v": "views"},
                ]
            }
        ]
        
        common_filters = [
            {
                "key": "filters",
                "name": "过滤",
                "value": [
                    {"n": "所有", "v": ""},
                    {"n": "单人作品", "v": "individual"},
                    {"n": "多人作品", "v": "multiple"},
                    {"n": "中文字幕", "v": "chinese-subtitle"},
                ]
            },
            {
                "key": "sort",
                "name": "排序",
                "value": [
                    {"n": "默认", "v": ""},
                    {"n": "发行日期", "v": "released_at"},
                    {"n": "最近更新", "v": "published_at"},
                    {"n": "收藏数", "v": "saved"},
                    {"n": "今日浏览", "v": "today_views"},
                    {"n": "本周浏览", "v": "weekly_views"},
                    {"n": "本月浏览", "v": "monthly_views"},
                    {"n": "总浏览", "v": "views"},
                ]
            }
        ]
        
        filters = {}
        filters["actresses"] = actress_filters
        
        for category in ["actresses/ranking", "genres", "makers"]:
            filters[category] = common_filters
        
        return {
            "class": categories,
            "filters": filters
        }

    def homeVideoContent(self):
        try:
            response = self._make_request("")
            html = response.text
            videos = self._parse_video_grid(html)
            return {
                'list': videos[:24]
            }
        except Exception as e:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, ext):
        try:
            if tid == "actresses":
                query_params = []
                
                if ext and isinstance(ext, dict):
                    if 'sort' in ext and ext['sort']:
                        query_params.append(f"sort={ext['sort']}")
                    
                    for key in ["height", "cup", "age", "debut"]:
                        if key in ext and ext[key]:
                            query_params.append(f"{key}={ext[key]}")
                
                if pg != "1":
                    query_params.append(f"page={pg}")
                
                url = "actresses"
                if query_params:
                    url = f"{url}?{'&'.join(query_params)}"
                
                response = self._make_request(url)
                html = response.text
                
                soup = BeautifulSoup(html, 'html.parser')
                items = self._parse_actress_list(soup)
                
                pagecount = self._extract_page_count(soup)
                
                return {
                    'list': items,
                    'page': int(pg),
                    'pagecount': pagecount or 9999,
                    'limit': 24,
                    'total': 999999
                }
            
            if tid.startswith('http') or '/actresses/' in tid:
                return self._get_actress_videos(tid, pg, ext)
            
            if self._is_specific_category_page(tid):
                return self._get_specific_category_videos(tid, pg, ext)
            else:
                return self._get_category_list(tid, pg, ext)
            
        except Exception as e:
            return {'list': []}
    
    def _parse_actress_list(self, soup):
        items = []
        
        actress_list = soup.find('ul', class_='mx-auto grid grid-cols-2 gap-4 gap-y-8 sm:grid-cols-4 md:gap-6 lg:gap-8 lg:gap-y-12 xl:grid-cols-6 text-center')
        
        if not actress_list:
            return items
        
        li_items = actress_list.find_all('li')
        
        for li in li_items:
            try:
                link = li.find('a', href=re.compile(r'/actresses/'))
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href:
                    continue
                
                vod_id = href
                
                name = ''
                h4 = li.find('h4', class_='text-nord13')
                if h4:
                    name = h4.get_text(strip=True)
                
                if not name:
                    img = li.find('img')
                    if img:
                        name = img.get('alt', '')
                
                if not name:
                    try:
                        parts = href.split('/')
                        if len(parts) >= 2:
                            name = unquote(parts[-1])
                    except:
                        pass
                
                cover = ''
                img = li.find('img')
                if img:
                    cover = img.get('src', '')
                    if cover:
                        cover = self._fix_url(cover)
                
                remarks = []
                p_tags = li.find_all('p', class_='text-nord10')
                for p in p_tags:
                    text = p.get_text(strip=True)
                    if text:
                        remarks.append(text)
                
                item = {
                    'vod_id': vod_id,
                    'vod_name': name or '女优',
                    'vod_pic': cover or '',
                    'vod_remarks': ' | '.join(remarks) if remarks else '女优',
                    'vod_tag': 'folder'
                }
                
                items.append(item)
                
            except:
                continue
        
        return items
    
    def _get_actress_videos(self, actress_url, pg, ext):
        try:
            query_params = []
            if ext and isinstance(ext, dict):
                if 'filters' in ext and ext['filters']:
                    query_params.append(f"filters={ext['filters']}")
                if 'sort' in ext and ext['sort']:
                    query_params.append(f"sort={ext['sort']}")
            
            if pg != "1":
                query_params.append(f"page={pg}")
            
            url = actress_url
            if query_params:
                url = f"{url}?{'&'.join(query_params)}"
            
            response = self._make_request(url)
            html = response.text
            
            videos = self._parse_video_grid(html)
            
            soup = BeautifulSoup(html, 'html.parser')
            pagecount = self._extract_page_count(soup)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount or 9999,
                'limit': 24,
                'total': 999999
            }
            
        except Exception as e:
            return {'list': []}
    
    def _parse_video_grid(self, html):
        videos = []
        seen_ids = set()
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            video_containers = []
            video_containers.extend(soup.find_all('div', class_='thumbnail group'))
            
            grid_selectors = [
                'div.grid.grid-cols-2.md\\:grid-cols-3.xl\\:grid-cols-4.gap-5',
                'div.grid.grid-cols-2.gap-4.md\\:grid-cols-3.xl\\:grid-cols-4',
                'div.grid.grid-cols-2.md\\:grid-cols-3.lg\\:grid-cols-4.gap-4',
            ]
            
            for selector in grid_selectors:
                grid = soup.select_one(selector)
                if grid:
                    for thumbnail in grid.find_all('div', class_='thumbnail group'):
                        if thumbnail not in video_containers:
                            video_containers.append(thumbnail)
                    break
            
            # 第一步：收集所有视频数据
            all_videos = []
            for container in video_containers:
                video_data = self._parse_video_item(container)
                if video_data:
                    all_videos.append(video_data)
            
            # 第二步：按番号分组
            video_groups = {}
            for video in all_videos:
                base_id = self._extract_base_video_id(video['vod_id'])
                if base_id:
                    if base_id not in video_groups:
                        video_groups[base_id] = []
                    video_groups[base_id].append(video)
            
            # 第三步：处理每个番号组
            for base_id, group_videos in video_groups.items():
                if base_id in seen_ids:
                    continue
                
                seen_ids.add(base_id)
                
                # 为每个域名生成选集
                play_from = []
                play_url = []
                
                for domain in self.domains:
                    domain_name = self._extract_domain_name(domain)
                    
                    # 构建该域名的视频URL
                    video_urls = []
                    for video in group_videos:
                        # 使用当前域名的完整URL
                        video_url = f"{domain}/{video['vod_id']}"
                        video_urls.append(f"{domain_name}${video_url}")
                    
                    if video_urls:
                        play_from.append(domain_name)
                        play_url.append('#'.join(video_urls))
                
                if play_from:
                    # 使用第一个视频作为显示视频
                    main_video = group_videos[0]
                    main_video['vod_play_from'] = '$$$'.join(play_from)
                    main_video['vod_play_url'] = '$$$'.join(play_url)
                    main_video['vod_remarks'] = f"{len(self.domains)}个域名"
                    videos.append(main_video)
                else:
                    # 如果没有找到任何视频，只添加第一个
                    video = group_videos[0]
                    videos.append(video)
            
            return videos
            
        except Exception as e:
            return []
    
    def _get_line_name(self, video_id):
        """获取线路名称（基于视频内容类型）"""
        if not video_id:
            return '有碼'
        
        video_id_lower = video_id.lower()
        
        if '-uncensored-leak' in video_id_lower:
            return '無碼'
        elif '-chinese-subtitle' in video_id_lower:
            return '中文字幕'
        else:
            return '有碼'
    
    def _extract_base_video_id(self, video_id):
        """提取视频的基础ID（去除版本后缀）"""
        if not video_id:
            return ''
        
        # 移除路径部分
        if '/' in video_id:
            video_id = video_id.split('/')[-1]
        
        # 移除常见后缀
        suffixes = ['-uncensored-leak', '-chinese-subtitle', '-ch', '-sub']
        base_id = video_id.lower()
        
        for suffix in suffixes:
            if base_id.endswith(suffix):
                base_id = base_id[:-len(suffix)]
        
        # 提取标准番号格式
        match = re.search(r'([a-z]+-\d+)', base_id)
        if match:
            return match.group(1)
        
        return base_id
    
    def _parse_video_item(self, thumbnail_div):
        try:
            video_link = None
            links = thumbnail_div.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                if self._is_video_link(href):
                    video_link = link
                    break
            
            if not video_link:
                return None
            
            href = video_link.get('href', '')
            vod_id = self._extract_video_id(href)
            if not vod_id:
                return None
            
            title = ''
            title_div = thumbnail_div.find('div', class_='my-2 text-sm text-nord4 truncate')
            if title_div:
                title_a = title_div.find('a')
                if title_a:
                    title = title_a.get_text(strip=True)
                else:
                    title = title_div.get_text(strip=True)
            
            if not title:
                img = thumbnail_div.find('img')
                if img:
                    title = img.get('alt', '')
            
            if not title:
                title = video_link.get_text(strip=True)
            
            if not title:
                title = vod_id.upper()
            
            cover = ''
            img = thumbnail_div.find('img')
            if img:
                cover = img.get('data-src') or img.get('src', '')
                if cover:
                    cover = self._fix_url(cover)
            
            duration = ''
            duration_span = thumbnail_div.find('span', class_='absolute bottom-1 right-1')
            if duration_span:
                duration = duration_span.get_text(strip=True)
            
            actors = []
            actor_div = thumbnail_div.find('div', class_='text-xs text-nord10 truncate')
            if actor_div:
                actor_links = actor_div.find_all('a')
                for actor_link in actor_links:
                    actor_name = actor_link.get_text(strip=True)
                    if actor_name and actor_name not in actors:
                        actors.append(actor_name)
            
            video_info = {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': cover or '',
                'vod_remarks': duration or vod_id.upper(),
                'vod_tag': 'video',
                'vod_actor': ' | '.join(actors) if actors else ''
            }
            
            return video_info
            
        except:
            return None
    
    def _is_specific_category_page(self, tid):
        patterns = [
            r'^dm\d+/actresses/.+$',
            r'^genres/.+$',
            r'^makers/.+$',
            r'^dm\d+/genres/.+$',
            r'^dm\d+/makers/.+$',
        ]
        
        for pattern in patterns:
            if re.match(pattern, tid):
                return True
        
        return False
    
    def _get_specific_category_videos(self, tid, pg, ext):
        try:
            query_params = []
            if ext and isinstance(ext, dict):
                if 'filters' in ext and ext['filters']:
                    query_params.append(f"filters={ext['filters']}")
                if 'sort' in ext and ext['sort']:
                    query_params.append(f"sort={ext['sort']}")
            
            if pg != "1":
                query_params.append(f"page={pg}")
            
            url = tid
            if query_params:
                url = f"{url}?{'&'.join(query_params)}"
            
            response = self._make_request(url)
            html = response.text
            
            videos = self._parse_video_grid(html)
            
            soup = BeautifulSoup(html, 'html.parser')
            pagecount = self._extract_page_count(soup)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount or 9999,
                'limit': 24,
                'total': 999999
            }
            
        except Exception as e:
            return {'list': []}
    
    def _get_category_list(self, tid, pg, ext):
        try:
            query_params = []
            if ext and isinstance(ext, dict):
                if 'filters' in ext and ext['filters']:
                    query_params.append(f"filters={ext['filters']}")
                if 'sort' in ext and ext['sort']:
                    query_params.append(f"sort={ext['sort']}")
            
            if pg != "1":
                query_params.append(f"page={pg}")
            
            url = tid
            if query_params:
                url = f"{url}?{'&'.join(query_params)}"
            
            response = self._make_request(url)
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            
            if tid in ["actresses/ranking"]:
                items = self._parse_actress_list(soup)
            elif tid == "genres":
                items = self._parse_genre_list(soup, tid)
            elif tid == "makers":
                items = self._parse_maker_list(soup, tid)
            else:
                items = []
            
            pagecount = self._extract_page_count(soup)
            
            return {
                'list': items,
                'page': int(pg),
                'pagecount': pagecount or 9999,
                'limit': 24,
                'total': 999999
            }
            
        except Exception as e:
            return {'list': []}
    
    def _parse_genre_list(self, soup, tid):
        items = []
        
        grid = soup.find('div', class_='grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4')
        if not grid:
            return items
        
        grid_items = grid.find_all('div', recursive=False)
        
        for item in grid_items:
            try:
                link = item.find('a', href=re.compile(r'/dm\d+/genres/'))
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href:
                    continue
                
                vod_id = href.lstrip('/')
                name = link.get_text(strip=True)
                
                item_info = {
                    'vod_id': vod_id,
                    'vod_name': name or '类型',
                    'vod_pic': '',
                    'vod_remarks': '类型',
                    'vod_tag': 'folder'
                }
                
                items.append(item_info)
                
            except:
                continue
        
        return items
    
    def _parse_maker_list(self, soup, tid):
        items = []
        
        grid = soup.find('div', class_='grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4')
        if not grid:
            return items
        
        grid_items = grid.find_all('div', recursive=False)
        
        for item in grid_items:
            try:
                link = item.find('a', href=re.compile(r'/dm\d+/makers/'))
                if not link:
                    continue
                
                href = link.get('href', '')
                if not href:
                    continue
                
                vod_id = href.lstrip('/')
                name = link.get_text(strip=True)
                
                item_info = {
                    'vod_id': vod_id,
                    'vod_name': name or '发行商',
                    'vod_pic': '',
                    'vod_remarks': '发行商',
                    'vod_tag': 'folder'
                }
                
                items.append(item_info)
                
            except:
                continue
        
        return items
    
    def _is_video_link(self, href):
        if not href:
            return False
        
        exclude_keywords = [
            '/actresses/', '/genres/', '/makers/', 
            '/search/', '/ranking', '?page=', '#', 
            'javascript:', '/series/', '/tags/'
        ]
        
        if any(keyword in href for keyword in exclude_keywords):
            return False
        
        video_pattern = r'[a-zA-Z]+-\d+'
        
        if '/' in href:
            last_part = href.rstrip('/').split('/')[-1]
            if '?' in last_part:
                last_part = last_part.split('?')[0]
            return bool(re.match(video_pattern, last_part))
        
        return bool(re.match(video_pattern, href))
    
    def _extract_video_id(self, href):
        if not href:
            return ''
        
        if '/' in href:
            last_part = href.rstrip('/').split('/')[-1]
            if '?' in last_part:
                last_part = last_part.split('?')[0]
            return last_part
        
        return href
    
    def _fix_url(self, url):
        if not url:
            return ''
        
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return self.base_url + url
        elif not url.startswith('http'):
            return f"{self.base_url}/{url}"
        
        return url
    
    def _extract_page_count(self, soup):
        try:
            pagination = soup.find('nav', class_=re.compile(r'flex items-center'))
            if pagination:
                links = pagination.find_all('a')
                max_page = 1
                for link in links:
                    href = link.get('href', '')
                    if 'page=' in href:
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            page_num = int(match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                return max_page if max_page > 1 else 1
            
            return 9999
            
        except:
            return 9999

    def detailContent(self, ids):
        vod_id = ids[0]
        
        try:
            # 如果vod_id是完整的URL，提取基础ID
            if vod_id.startswith('http'):
                parsed = urlparse(vod_id)
                vod_id = parsed.path.lstrip('/')
            
            base_id = self._extract_base_video_id(vod_id)
            
            # 访问有码版页面获取详情（只检查第一个域名）
            main_url = base_id
            response = self._make_request(main_url)
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            detail_info = self._extract_video_detail(soup, base_id)
            
            # 只需要检查第一个域名的各种版本
            test_domain = self.domains[0]
            available_versions = []
            
            # 基础版本（有码）
            base_url = f"{test_domain}/{base_id}"
            available_versions.append(f"有碼${base_url}")
            
            # 无码版本
            uncensored_url = f"{test_domain}/{base_id}-uncensored-leak"
            try:
                # 快速检查，设置较短的超时时间
                test_resp = requests.head(uncensored_url, timeout=2, allow_redirects=True)
                if test_resp.status_code < 400:
                    available_versions.append(f"無碼${uncensored_url}")
            except:
                pass
            
            # 中文字幕版本
            subtitle_url = f"{test_domain}/dm2/{base_id}-chinese-subtitle"
            try:
                test_resp = requests.head(subtitle_url, timeout=2, allow_redirects=True)
                if test_resp.status_code < 400:
                    available_versions.append(f"中文字幕${subtitle_url}")
            except:
                pass
            
            # 构建5个域名各自的选集（基于相同的版本结构）
            play_from = []
            play_url = []
            
            for domain in self.domains:
                domain_name = self._extract_domain_name(domain)
                
                # 基于第一个域名的可用版本，为当前域名构建播放链接
                domain_versions = []
                for version in available_versions:
                    version_name, version_url = version.split('$', 1)
                    # 提取版本后缀
                    version_suffix = version_url.split('/')[-1].replace(base_id, '')
                    # 构建当前域名的版本URL
                    domain_version_url = f"{domain}/{base_id}{version_suffix}"
                    domain_versions.append(f"{version_name}${domain_version_url}")
                
                if domain_versions:
                    play_from.append(domain_name)
                    play_url.append('#'.join(domain_versions))
            
            if play_from:
                detail_info['vod_play_from'] = '$$$'.join(play_from)
                detail_info['vod_play_url'] = '$$$'.join(play_url)
                detail_info['vod_remarks'] = f"{len(play_from)}个域名可用 | {len(available_versions)}个版本"
            else:
                # 回退到基础版本
                line_name = self._get_line_name(base_id)
                detail_info['vod_play_from'] = line_name
                detail_info['vod_play_url'] = f"{line_name}${self.base_url}/{base_id}"
            
            return {
                'list': [detail_info]
            }
            
        except Exception as e:
            # 如果无法获取详情，返回基本格式
            line_name = self._get_line_name(vod_id)
            return {
                'list': [{
                    'vod_id': vod_id,
                    'vod_name': vod_id.upper(),
                    'vod_pic': '',
                    'vod_play_from': line_name,
                    'vod_play_url': f'{line_name}${vod_id}',
                    'vod_remarks': line_name
                }]
            }
    
    def _extract_video_detail(self, soup, video_id):
        try:
            title = ""
            h1_tag = soup.find('h1', class_=re.compile(r'text-2xl|text-3xl|text-4xl'))
            if not h1_tag:
                h1_tag = soup.find('title')
            
            if h1_tag:
                title = h1_tag.get_text(strip=True)
                if ' - ' in title:
                    title = title.split(' - ')[0]
            
            cover = ""
            img = soup.find('img', class_=re.compile(r'object-cover|w-full|rounded-lg'))
            if not img:
                img = soup.find('img', alt=re.compile(title))
            
            if img:
                cover = self._fix_url(img.get('src', ''))
            
            tags = []
            tag_elements = soup.find_all('a', href=re.compile(r'/dm\d+/genres/|/series/'))
            for tag in tag_elements:
                tag_text = tag.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            
            actors = []
            actor_elements = soup.find_all('a', href=re.compile(r'/dm\d+/actresses/'))
            for actor in actor_elements:
                actor_text = actor.get_text(strip=True)
                if actor_text and actor_text not in actors:
                    actors.append(actor_text)
            
            maker = ""
            maker_element = soup.find('a', href=re.compile(r'/dm\d+/makers/'))
            if maker_element:
                maker = maker_element.get_text(strip=True)
            
            duration = ""
            duration_element = soup.find('span', class_=re.compile(r'duration|time|length|text-sm'))
            if duration_element:
                duration = duration_element.get_text(strip=True)
            
            pub_date = ""
            date_elements = soup.find_all('p', class_=re.compile(r'text-sm'))
            for elem in date_elements:
                text = elem.get_text(strip=True)
                if '發行日期' in text or '配信開始日' in text or '発売日' in text:
                    pub_date = text.replace('發行日期：', '').replace('配信開始日：', '').replace('発売日：', '')
                    break
            
            code = video_id.upper() if video_id else ""
            
            description = []
            if actors:
                description.append(f"演员: {' | '.join(actors)}")
            if tags:
                description.append(f"类型: {' | '.join(tags)}")
            if maker:
                description.append(f"发行商: {maker}")
            if code:
                description.append(f"番号: {code}")
            if duration:
                description.append(f"时长: {duration}")
            if pub_date:
                description.append(f"发行日期: {pub_date}")
            
            return {
                'vod_id': video_id,
                'vod_name': title or video_id,
                'vod_pic': cover,
                'type_name': ' | '.join(tags[:3]) if tags else '日本AV',
                'vod_year': pub_date[:4] if pub_date and len(pub_date) >= 4 else '',
                'vod_area': '日本',
                'vod_remarks': duration or code or 'MissAV2',
                'vod_actor': ' | '.join(actors[:5]) if actors else '',
                'vod_director': maker or '',
                'vod_content': ' | '.join(description) if description else '日本AV作品'
            }
            
        except Exception as e:
            return {
                'vod_id': video_id,
                'vod_name': video_id,
                'vod_pic': ''
            }

    def searchContent(self, key, quick, pg="1"):
        try:
            encoded_key = quote(key)
            url = f"search/{encoded_key}"
            if pg != "1":
                url = f"{url}?page={pg}"
            
            response = self._make_request(url)
            html = response.text
            
            videos = self._parse_video_grid(html)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': 9999,
                'limit': 30,
                'total': 999999
            }
            
        except Exception as e:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            if '$' in id:
                # 处理多个版本的情况
                parts = id.split('$')
                if len(parts) > 1:
                    video_url = parts[1]
                    # 如果video_url是相对路径，添加域名
                    if not video_url.startswith('http'):
                        video_url = self.base_url + '/' + video_url.lstrip('/')
                else:
                    video_url = id
            else:
                video_url = id
            
            # 如果不是完整URL，添加当前域名
            if not video_url.startswith('http'):
                video_url = self.base_url + '/' + video_url.lstrip('/')
            
            return {
                'parse': 1,
                'url': video_url,
                'header': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': f'{self.base_url}/',
                }
            }
            
        except Exception as e:
            return {
                'parse': 1,
                'url': f"{self.base_url}",
                'header': self.session.headers
            }

    def isVideoFormat(self, url):
        if any(keyword in url for keyword in ['/actresses/', '/genres/', '/makers/']):
            return False
        if re.match(r'[a-zA-Z]+-\d+', url):
            return True
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        if hasattr(self, 'session'):
            self.session.close()

    def localProxy(self, param):
        return []