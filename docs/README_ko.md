# Agent Reach

Agent Reach는 10개 인터넷 플랫폼의 상위 도구를 설치·설정·진단하는 capability
layer입니다. 통합 `read`/`search` 래퍼가 아닙니다. 에이전트는
`agent-reach doctor --json`의 `active_backend`를 직접 호출합니다.

지원 채널: GitHub, Twitter/X, YouTube, Reddit, Bilibili(공개 검색 API만),
LinkedIn, V2EX, RSS, Exa Search, Web. Exa는 mcporter를 통해 API key 없이
사용하며 Reddit은 로그인이 필요합니다. `doctor`는 기본적으로 오프라인이며,
Web/Exa/Bilibili/V2EX/LinkedIn처럼 외부 네트워크 요청을 하는 프로브는
`--live`를 사용할 때만 실행됩니다.

## 안전한 설치

```bash
python -m pip install "agent-reach==1.5.0"
agent-reach install --env=auto                 # 읽기 전용 계획
agent-reach install --env=auto --dry-run       # 쓰기 없음
agent-reach install --env=auto --yes            # 검토 후 승인
```

Agent Reach는 sudo, OS 패키지 관리자, 다운로드한 setup script를 자동 실행하지
않습니다. `doctor`도 완전히 읽기 전용입니다.

Cookie/API key를 argv, 셸 기록, 채팅 또는 로그에 넣지 마세요.

```bash
agent-reach configure groq-key
printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin
```

자격 증명 파일은 기존 0644 파일도 owner-only로 원자적으로 교체합니다. GitHub
token은 `gh`가 저장하며 Agent Reach는 복사본을 보관하지 않습니다.

## 진단과 스킬

```bash
agent-reach doctor --live
agent-reach doctor --json
agent-reach skill --install
```

사용자 정의 skill은 `--force` 없이는 덮어쓰지 않습니다. 패키지 skill은
fetch-only이며 가져온 콘텐츠를 신뢰하지 않고 정확한 host 검증, 출력 제한, 비밀
보호를 적용합니다. 모든 쓰기 작업은 별도의 명시적 승인이 필요합니다.

자세한 내용은 [영문 README](README_en.md), [설치 가이드](install.md),
[업데이트 가이드](update.md)를 참고하세요.
