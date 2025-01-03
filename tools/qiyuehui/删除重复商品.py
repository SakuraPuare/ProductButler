import sys
import pathlib
import pandas as pd

sys.path.append(
    str(pathlib.Path(__file__).parent.parent.parent)
)

async def main():
    df = pd.read_excel('goods_list.xlsx')

    df.sort_values(by='addTime', inplace=True)

    # Group by goodsSn and name, keep first occurrence
    duplicates = df[df.duplicated(subset=['goodsSn', 'name'], keep='first')]
    
    # Get the IDs of duplicates to delete
    duplicate_ids = duplicates['id'].tolist()

    print(f"Found {len(duplicate_ids)} duplicate items to delete")

    # Import delete_goods function
    from upload.qiyuehui.apis import delete_goods

    # Delete duplicates
    for goods_id in duplicate_ids:
        try:
            await delete_goods(goods_id)
            print(f"Deleted goods ID: {goods_id}")
        except Exception as e:
            print(f"Error deleting goods ID {goods_id}: {str(e)}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
