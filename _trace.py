"""
Quick end-to-end trace — runs the full analysis pipeline on a real PR
and prints exactly where it fails.
"""
import sys, asyncio, traceback
sys.path.insert(0, ".")

async def main():
    # Use a known public PR from your own account
    from backend.config import get_settings
    s = get_settings()
    print(f"Provider: {s.default_llm_provider.value}")
    print(f"Groq key: {'SET' if s.groq_api_key else 'MISSING'}")
    print(f"GitHub token: {'SET' if s.github_token else 'MISSING'}")
    print()

    # Step 1: fetch user repos to find a valid PR
    import httpx
    token = s.github_token.get_secret_value() if s.github_token else ""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.github.com/user/repos?sort=updated&per_page=10",
            headers=headers
        )
        repos = r.json()
        print("Your repos:")
        for repo in repos[:5]:
            print(f"  {repo['full_name']} (private={repo['private']})")

        # Find first repo with open PRs
        target_pr_url = None
        for repo in repos[:10]:
            r2 = await client.get(
                f"https://api.github.com/repos/{repo['full_name']}/pulls?state=open&per_page=3",
                headers=headers
            )
            prs = r2.json() if r2.status_code == 200 else []
            if prs:
                target_pr_url = prs[0]["html_url"]
                print(f"\nFound open PR: {target_pr_url}")
                break

    if not target_pr_url:
        print("\nNo open PRs found in your repos. Create one to test.")
        return

    # Step 2: run full analysis
    print("\nRunning analysis...")
    from backend.services.analysis_service import AnalysisService
    service = AnalysisService()
    try:
        result = await service.analyse(
            pr_url=target_pr_url,
            enable_rag=False,
            skip_rag_indexing=True,
        )
        print(f"\nVerdict: {result.verdict}")
        print(f"Confidence: {result.confidence_score:.0%}")
        print(f"Summary: {result.primary_reasoning[:200]}")
        print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"\nANALYSIS FAILED:")
        traceback.print_exc()

asyncio.run(main())
