"""Quick check after pasting Supabase keys into .streamlit/secrets.toml"""

from supabase_config import get_supabase_credentials, is_supabase_configured
from supabase_store import _rpc_available, list_tracked_products


def main():
    if not is_supabase_configured():
        print('Supabase keys are missing or still placeholders.')
        print('Edit: .streamlit/secrets.toml')
        return

    url, _ = get_supabase_credentials()
    print(f'Using Supabase project: {url}')

    try:
        rows = list_tracked_products()
    except Exception as exc:
        message = str(exc)
        if 'PGRST205' in message or 'tracked_products' in message:
            print('\nSupabase keys are working, but the table is not created yet.')
            print('Create it once in Supabase:')
            print('  1. Open https://supabase.com/dashboard')
            print('  2. SQL Editor -> New query')
            print('  3. Paste SQL from: supabase/01_fresh_install.sql (or schema.sql)')
            print('  4. Then run: supabase/03_rpc_functions.sql')
            print('  5. Run again: python check_supabase.py')
            return
        print(f'\nSupabase error: {exc}')
        return

    print('Supabase connection OK.')
    print(f'Tracked products in database: {len(rows)}')
    if _rpc_available():
        print('RPC functions: installed (single-call list/upsert/batch).')
    else:
        print('RPC functions: not installed yet.')
        print('  Run supabase/03_rpc_functions.sql in Supabase SQL Editor for fewer API calls.')


if __name__ == '__main__':
    main()
