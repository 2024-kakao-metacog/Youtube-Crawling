Youtube Shorts의 Metadata를 자동으로 Crawling 해주는 코드입니다.

# 개발환경

- `Python 3.11`
- `beautifulsoup 4.12.3`
- `selenium 4.27.1`

# 수집 데이터(Example)

> - currentURL(String): https://www.youtube.com/shorts/9zIZz1kdfo
> - thumbnailURL(String): https://i.ytimg.com/vi/9zIZz1kdfo/oardefault.jpg?sqp=-oaymwEdAFSFWQAgHywwIARUAAIhCcAHAAQY=&rs=AOn4MMlcUG5DCOfB91p8COsTy2jRHRA
> - userName(String): @Dopameme
> - likeCount(String): 42만
> - commentCount(String): 103만
> - title(String): Youtube Shorts Crawling?!
> - description(String): Huh?
> - publishedAt(ISO 8601): 2024-08-15T08:00:10-07:00
> - viewCount(Int): 206983590

# 실행방법

```
python3.11 -m venv .venv # 가상환경 생성

source .venv/bin/activate # 가상환경 실행

pip install -r requirements.txt # 실행에 필요한 모든 패키지 설치

python3.11 metadata_crawling.py # 크롤링 스크립트 실행
```
