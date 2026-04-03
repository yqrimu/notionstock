#!/usr/bin/env python3
"""
Insert Trading Research entries with resistance, support, buy/sell points, and notes.
"""

import os
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from obsidian_sync import ObsidianWriter

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
STOCKS_DB_ID = "20be24d8-7d14-818a-9586-e5478b4e6c18"
TRADING_RESEARCH_DB_ID = "20be24d8-7d14-8129-975e-e2624faaaad9"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Initialize Obsidian writer
obsidian_writer = ObsidianWriter(
    stocks_path=os.getenv('OBSIDIAN_STOCKS_PATH'),
    trading_research_path=os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH')
)

def get_stock_id_by_ticker(ticker):
    """Get stock page ID by ticker symbol"""
    url = f"https://api.notion.com/v1/databases/{STOCKS_DB_ID}/query"

    payload = {
        "filter": {
            "property": "Ticker",
            "title": {
                "equals": ticker
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if data.get("results"):
        return data["results"][0]["id"]
    return None

def create_trading_research_entry(date, ticker, resistance, support, buy_point, sell_point, ladder, notes):
    """Create a new Trading Research entry"""

    # Get stock ID
    stock_id = get_stock_id_by_ticker(ticker)
    if not stock_id:
        print(f"✗ Stock {ticker} not found in Stocks database")
        return False

    # Build properties
    properties = {
        "Notes": {
            "title": [{"text": {"content": notes}}]
        },
        "Date": {
            "date": {"start": date}
        },
        "Stock 1": {
            "relation": [{"id": stock_id}]
        }
    }

    # Add optional numeric/text fields
    if resistance:
        properties["Resistance"] = {"rich_text": [{"text": {"content": str(resistance)}}]}

    if support:
        properties["Support"] = {"rich_text": [{"text": {"content": str(support)}}]}

    if buy_point:
        properties["Buy Point"] = {"rich_text": [{"text": {"content": str(buy_point)}}]}

    if sell_point:
        properties["Sell Point"] = {"rich_text": [{"text": {"content": str(sell_point)}}]}

    if ladder:
        properties["Ladder"] = {"number": float(ladder) if isinstance(ladder, (int, float)) else float(ladder.split("-")[0])}

    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": TRADING_RESEARCH_DB_ID},
        "properties": properties
    }

    # Insert to Notion first (primary operation)
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        notion_id = response.json()['id']

        # Insert to Obsidian (non-blocking)
        try:
            filename = obsidian_writer.generate_trading_research_filename(
                ticker=ticker.replace("$", ""),
                date=date,
                resistance=resistance,
                support=support,
                buy_point=buy_point,
                sell_point=sell_point,
                notes=notes
            )

            obsidian_writer.write_trading_research_entry(
                filename=filename,
                notion_id=notion_id,
                properties={
                    'date': date,
                    'ticker': ticker,
                    'resistance': resistance,
                    'support': support,
                    'buy_point': buy_point,
                    'sell_point': sell_point,
                    'ladder': ladder,
                    'notes': notes
                }
            )
        except Exception as e:
            logger.warning(f"Obsidian insert failed (non-blocking): {str(e)}")

        print(f"✓ Created entry for {ticker}")
        return True
    else:
        print(f"✗ Failed to create entry for {ticker}: {response.text}")
        return False

# Entries to insert (add new entries here, then move to archive below after running)
entries = [
    # Format: (date, ticker, resistance, support, buy_point, sell_point, ladder, notes)

    # 人性之本 2026-03-31 Session
    ("2026-03-31T12:45:00", "$TSLA", None, None, None, None, 369, "站稳369就安全了，说过多次，今年重点Tsll和msfl"),
    ("2026-03-31T13:09:00", "$MULL", None, None, None, None, 103.7, "今天要减仓，如果突破不了103.7。Mu是好股只不过要大洗盘，Mu 2倍可以按照操盘手意图多做几次波段"),

    # 人性之本 2026-04-01 Session
    ("2026-04-01T09:50:00", "$TSLA", None, "371-373", None, None, None, "特斯拉支撑371-373"),
    ("2026-04-01T09:50:00", "$NVDA", None, "174", None, None, None, "Nvda支撑174"),
    ("2026-04-01T09:59:00", "$MSFT", None, "367", None, None, None, "Msft支撑367"),
    ("2026-04-01T09:59:00", "$MSTR", None, "121", None, None, None, "Mstr支撑121"),
    ("2026-04-01T12:15:00", "$NFXL", None, None, "20.88", None, None, "预设20.88买nfxl，到不了不做，一直到月底有效"),
    ("2026-04-01T12:28:00", "$TSLQ", None, None, "17.88-18.18", None, None, "未来几天可能要少买tslq，这个是做对冲的，预设17.88-18.18买一单，一直到明天，设止损一半，防止到水里"),
    ("2026-04-01T12:35:00", "$HIMZ", "25-37", None, None, None, None, "25-37有大量小散被套，不容易解套。减仓第一次20%，第二次30-40%，就不再减。接只接回20%仓位，大跌再接回30%，这样你会无所谓涨跌"),
    ("2026-04-01T12:35:00", "$SQQQ", None, None, "66.98", None, None, "心里容易慌的就买保险，保险千万别买半山腰会两边挨打，少买点sqqq在66.98"),
    ("2026-04-01T13:09:00", "$METU", None, None, None, "23.88", None, "到23.88（截图确认），Metu到达23.88卖点"),
    ("2026-04-01T13:34:00", "$TSLL", None, None, None, None, 12.8, "Tsll这2天很关键，12.8太重要"),
    ("2026-04-01T13:48:00", "$AXTI", None, None, "44", None, None, "不知道群里有没有人买过，如果到44，少买一点"),
    ("2026-04-01T13:48:00", "$MU", None, None, None, None, 383, "完全是挤空，趋势价格是383，不站稳都当反弹"),
    ("2026-04-01T15:18:00", "$HIMS", None, None, "19.58", None, None, "它在洗盘，分2次加仓：19.58和17.88，第一加仓都不要买多"),
    ("2026-04-01T15:28:00", "$HIMS", None, None, "17", None, None, "风险比较大的股，中国白人平台都被套很多。预设19.58临时改主意市场价买了一点，不到17左右就不加了"),

    # 人性之本 2026-04-02 Session
    ("2026-04-02T10:02:00", "$TSLL", None, None, "10.88-11.18", None, None, "预设10.88-11.18买tsll"),
    ("2026-04-02T10:11:00", "$MULL", None, None, "105.18", None, 121, "今天是洗盘不是跌，昨天减仓的2倍今天可以买回来，预设105.18买mull，正常应该超过121"),
    ("2026-04-02T10:46:00", "$APPX", None, None, None, "26.98", None, "买到appx的预设26.98卖一半，底仓不卖，原因是app今天出现了买点"),
    ("2026-04-02T10:59:00", "$METU", None, None, "20.88", None, None, "预设20.88接回昨天23.88减仓的metu，有效到4月7号"),
    ("2026-04-02T11:38:00", "$MULL", None, None, "312, 298", None, None, "Mu股票不用卖，Mull底仓留着，311基本是波段底（MU股票价格触发点），当MU到达312或298时买入MULL，预设一直到4月底，到不了再改市场价"),
    ("2026-04-02T12:21:00", "$AMDL", None, None, None, "13.7", None, "预设一单13.7减仓amdl，底仓不打算卖"),
    ("2026-04-02T12:21:00", "$MSFL", None, None, "14.18", None, None, "预设14.18接回msfl，这个2倍也相信会涨不是一点。收盘前39分钟或盘后大跌可以买，但要留现金，2倍做勤快一点"),
    ("2026-04-02T14:20:00", "$MULL", None, None, None, None, 121, "做形态，收盘站稳121就做成了"),
    ("2026-04-02T15:50:00", "$SBET", None, None, "5.28", None, None, "预设5.28买sbet，一直到月底"),
]

# ARCHIVED: 2026-03-30 entries (already inserted)
archived_entries_20260330 = [
    # Format: (date, ticker, resistance, support, buy_point, sell_point, ladder, notes)

    # 人性之本 2026-03-30 Session 1 (9:48 AM - 3:21 PM)
    ("2026-03-30T09:48:00", "$MU", None, "339", None, None, None, "Mu是大洗盘，不破339都没事，我们这里是做波段，管住自己"),
    ("2026-03-30T09:48:00", "$MULL", None, None, "110.66", None, None, "预设110.66买mull，做波段，管住自己"),
    ("2026-03-30T09:48:00", "$AVGO", None, None, "289.18", None, None, "预设289.18买avgo"),
    ("2026-03-30T09:48:00", "$CRWV", None, None, "70.88-71.18", None, None, "预设70.88-71.18买一单crwv"),
    ("2026-03-30T09:56:00", "$AAPL", None, None, "231", None, None, "苹果一直没说因为在等244，但这个价格也不想做，231可能要考虑"),
    ("2026-03-30T09:56:00", "$CRWV", None, "67", "64", None, None, "到水里去了反弹就走，不到64不再买，67有支撑"),
    ("2026-03-30T10:23:00", "$MU", None, None, "108.88", None, None, "今天是砸盘，分2批进，第二单108.88，股市没有安全，分批卖2倍"),
    ("2026-03-30T10:23:00", "$TSLL", None, None, None, None, 369, "以特斯拉369为准"),
    ("2026-03-30T10:30:00", "$MULL", None, None, None, None, None, "又复盘了mu觉得是大洗盘，哪怕mull破100，今年以tsll和msfl 2倍为重点，国内尽量买大股票，等买avgo，Tsm；sndk建仓不破500不买；Mu破100那真的美股要出大事了，这种概率基本是5%"),
    ("2026-03-30T10:30:00", "$SNDK", None, None, None, None, 500, "建仓，不破500，不买"),
    ("2026-03-30T10:38:00", "$NVDL", None, None, "64.98-65.28", None, None, "预设64.98-65.28买一单Nvdl；Alab一直等了这么久今天到了，以前看回调价格，今天感觉整个股市不好可能还有一腿，不要多操作"),
    ("2026-03-30T10:38:00", "$ALAB", None, None, None, None, None, "一直等了这么久今天到了，以前看到是因为看回调价格，今天感觉整个股市不好可能还有一腿，不要多操作"),
    ("2026-03-30T10:47:00", "$MU", None, "339", None, None, None, "击穿339今天情况特殊所以没什么；盘感：如果是阴跌339一破就完蛋，如果当天是有人砸盘就不怕"),
    ("2026-03-30T11:14:00", "$NBIL", None, None, "8.18-8.28", None, None, "给没有时间差的，预设nbil 8.18-8.28"),
    ("2026-03-30T11:21:00", "$MU", None, None, None, None, None, "今天砸的太厉害了，现在不动，多空交战还没到，看它收盘前"),
    ("2026-03-30T11:21:00", "$ALAB", None, None, "102", None, None, "我看的就是102，今天可以买，加仓价我不喊不加，股票价格是等出来的"),
    ("2026-03-30T11:58:00", "$MU", None, None, None, None, None, "被空方拿下来了，现在别动，因为今天是砸盘，做好砸到330的准备"),
    ("2026-03-30T11:58:00", "$MULL", None, None, "104", None, None, "再加一仓mull 104块多"),
    ("2026-03-30T12:11:00", "$MULL", None, "97", None, None, None, "心里的底是97左右，174-188被套了一大批小散，正常走法要到星期三收盘前或星期四才能站稳"),
    ("2026-03-30T12:29:00", "$AMDL", None, None, "10.98-11.18", None, None, "在那边说amd，这边预设10.98-11.18买Amdl，炒股有缘份，2次止损就不要做了"),
    ("2026-03-30T13:28:00", "$TSLL", None, "11.2", None, None, None, "11.2 tsll支撑"),
    ("2026-03-30T14:06:00", "$MP", None, None, "44.88-45.28", None, None, "谁手上有mp，mp预设44.88-45.28，手上没有的不要买"),
    ("2026-03-30T14:06:00", "$TSM", None, None, "298.88-299.18", None, None, "不记得前面有没有提过，预设298.88-299.18建仓，第二单到270左右再说"),
    ("2026-03-30T14:19:00", "$TSLL", None, None, None, None, None, "今天tsll值得一赌，就是现在多空交战"),
    ("2026-03-30T14:27:00", "$TSLL", None, None, "10.75", None, None, "预设10.75加一仓tsll，这单设止损，本来是安全的，trump老要拿下伊朗油，消息在左右股市，都留点钱，到现在都没卖掉"),
    ("2026-03-30T14:41:00", "$SPX", "6344-6345.9", None, None, None, None, "大盘6344-6345.9，下面还有一个形态，多空交战没到，快收盘前一个小时操作设好止损，包括股票和2倍；昨晚特斯拉打到过一次355拉起来了，今天到了355.22"),
    ("2026-03-30T15:04:00", "$TSLA", None, None, None, None, None, "空头拿下来了，先不慌动"),
    ("2026-03-30T15:04:00", "$TSLL", None, None, "10.45", None, None, "特斯拉空头拿下来了，把10.72那一笔改成10.45"),
    ("2026-03-30T15:13:00", "$MULL", None, None, "95.88", None, None, "加一单95.88买mull，大概率要反弹到101，不到95.88改市场价，看收盘前，今天是精准砸盘"),
    ("2026-03-30T15:21:00", "$QQQ", None, None, None, None, 554.8, "Qqq是要搬运出去的，554.8是多方价格，都是趋势价格"),
    ("2026-03-30T15:21:00", "$SPX", None, None, None, None, 6322, "6322是多方价格，只要站稳6322收盘就行"),

    # 人性之本 2026-03-30 Session 2 (9:38 AM - 1:46 PM)
    ("2026-03-30T09:38:00", "$TSLA", None, "361", None, None, None, "特斯拉361是支撑，破了也没事"),
    ("2026-03-30T09:38:00", "$NVDA", None, "166.8", None, None, 165, "Nvda支撑166.8，如果不破165，买"),
    ("2026-03-30T09:38:00", "$MSFT", "517", "357", None, None, None, "Msft支撑357，极限517昨晚去了一次"),
    ("2026-03-30T09:38:00", "$GOOG", None, "271-273", None, None, None, "Goog支撑271-273"),
    ("2026-03-30T09:38:00", "$AMD", None, "201-203", None, None, None, "Amd支撑201-203"),
    ("2026-03-30T09:38:00", "$MSTR", None, None, None, None, 122, "Mstr只要在122以上都没事"),
    ("2026-03-30T09:38:00", "$ASST", None, "9.7", None, None, None, "今天支撑9.7，不建议操作，这个股给它6个星期，大跌才加仓"),
    ("2026-03-30T10:57:00", "$MSFT", None, None, None, None, None, "股票不用卖，2倍的有利，减仓"),
    ("2026-03-30T11:45:00", "$AMD", None, None, None, None, 194, "支撑破了，不破194就买2倍（AMDL），上个星期说的metu，就是冲着meta那么砸，都没有让空方拿下来"),
    ("2026-03-30T11:45:00", "$METU", None, None, None, None, None, "上个星期说的metu，就是冲着meta那么砸，都没有让空方拿下来"),
    ("2026-03-30T13:14:00", "$METU", None, None, None, None, 20.2, "记得减仓，站稳20.2才拿着"),
    ("2026-03-30T13:46:00", "$TSLL", None, None, None, None, None, "今天可以加一单tsll，设止损"),
]

if __name__ == "__main__":
    print(f"Starting insertion of {len(entries)} trading research entries...")

    success_count = 0
    failed_count = 0

    for entry in entries:
        date, ticker, resistance, support, buy_point, sell_point, ladder, notes = entry

        if create_trading_research_entry(date, ticker, resistance, support, buy_point, sell_point, ladder, notes):
            success_count += 1
        else:
            failed_count += 1

        # Small delay to respect rate limits
        time.sleep(0.3)

    print(f"\nCompleted!")
    print(f"Successfully created: {success_count} entries")
    print(f"Failed: {failed_count} entries")

# ARCHIVED: 2026-03-29 entries (already inserted)
archived_entries_20260329 = [
    ("2026-03-29T10:37:00", "$MULL", None, None, "105.18", None, None, "预设mull 105.18到4月15号"),
    ("2026-03-29T10:44:00", "$TSLL", None, None, "10.98", None, None, "预设tsll 10.98到星期四"),
    ("2026-03-29T10:44:00", "$TSLL", None, None, "9.98", None, None, "再预设一单9.98到4月15号"),
    ("2026-03-29T10:44:00", "$META", None, None, "481.18", None, None, "Meta 第一次买股票481.18"),
    ("2026-03-29T12:17:00", "$MU", None, None, "297.88", None, None, "现在预设297.88买mu，一直到4月30号"),
    ("2026-03-29T12:17:00", "$MSFT", None, None, "288-292", None, None, "Msft 在345有买点，但我觉得加仓的价格选择288-292比较好，这里有过大洗盘"),
    ("2026-03-29T12:17:00", "$AMZN", None, None, "185-189", None, None, "Amzn 到185-189买，也别买多，我自己打算破170多买"),
    ("2026-03-29T12:24:00", "$AMDL", None, None, "10.2", None, None, "重点股票，平时做tsll，Amdl 到10.2才多买"),
    ("2026-03-29T12:34:00", "$QQQM", None, None, "212.88", None, None, "其实买voo和qqqm是最稳的，缺点就是占有资金，赚的百分比不大，优势是大概率不会亏钱；Qqqm分2次买，212.88建仓，第二仓等哪天一个大跌，这个大跌不应该是战争，是跟trump本人有关，选举或者影响到他地位的什么"),
    ("2026-03-29T12:34:00", "$LLY", None, None, "719-722", None, None, "Lly是一个好股票，但是拼的是价格，不到719-722就不买"),
    ("2026-03-29T12:42:00", "$TSLL", None, "11.18-11.38", None, None, None, "我给的都是把风险全考虑进去了，实际上短期的tsll,11.38,11.18都有支撑，我是想给你们买到股票好的价格，2倍的想做，tsll可以来回做"),
    ("2026-03-29T12:42:00", "$AMDL", None, "11.48", None, None, None, "Amdl 11.48都有支撑，我是想给你们买到股票好的价格，2倍的想做，amdl可以来回做"),
    ("2026-03-29T14:01:00", "$TSLL", None, None, None, "12.98", None, "我在复盘，Tsll 预设12.98减仓"),
    ("2026-03-29T14:01:00", "$NVDA", None, None, "153.88", None, None, "Nvda 预设153.88买"),
    ("2026-03-29T19:26:00", "$MSFT", None, None, "344.8", None, None, "复盘一个说一个，Msft股票可以344.8，334.18买"),
    ("2026-03-29T19:26:00", "$MSFL", None, None, "13.18", "13.88-14.1", None, "Msfl这个走的就是当年的goog 2倍，短期预设13.88-14.1有赚就走；预设一笔卖单15.98-16.2减仓的；等待13.18再买；这个以后会涨的，13.88-14.1是有赚就走，预设15.98的是波段价格2笔，以后大概率超过18.6"),
    ("2026-03-29T19:45:00", "$MSFT", None, None, None, None, None, "我复盘msft很感叹，这也是我们今后要坚持做波段、减少操作的原因；战争、消息、财报都是表面的东西，实际上股市就像经济周期一样，到了高峰就是衰退然后开始新的一轮；不过这次跟以往不同的是，2个星期前开始，一直有资金加入做空"),
    ("2026-03-29T20:25:00", "$TSLA", None, None, None, None, None, "夜盘特斯拉以355.6为参考，确切地说，355.6-355.9"),
    ("2026-03-29T21:12:00", "$METU", None, None, None, "20", "20", "预设极限是操作的一个技巧，就是让自己涨跌都不慌，先建一个仓然后就等极限，极限到不了改市场价买；Metu突破不了20，卖；大盘可以做，一定要设好止损"),
    ("2026-03-29T23:05:00", "$TSLL", None, None, "11.18", None, None, "今明2天最合适的就是我提到的tsll，那个11.18破了一次，是比较好的价格"),
    ("2026-03-29T23:05:00", "$TSLA", None, "349", None, None, None, "特斯拉355破了也没关系，349不能破"),
]

# ARCHIVED: 2026-03-23 entries (already inserted)
archived_entries_20260323 = [
    ("2026-03-23T09:34:00", "$TSLA", None, None, None, None, "369", "短期趋势369，破了没事，早上大跌，没有破中期趋势。不突破379-382，减tsll"),
    ("2026-03-23T09:34:00", "$TSLL", None, None, None, None, None, "不突破tsla 379-382，减仓。2倍的有赚分批卖，手上要有现金"),
    ("2026-03-23T09:34:00", "$NVDL", None, None, "69", None, None, "提醒过2次前低169(nvda)，早上没有击穿，上个星期五说过，到69才加仓"),
    ("2026-03-23T09:41:00", "$MSFT", "387-389.6", None, None, None, None, "一直看好，复盘后改变主意做2倍，有赚就走，好的股票是拼价格，争取拿到低价格。阻力387-389.6。今天没有消息大概率涨盘"),
    ("2026-03-23T09:41:00", "$METU", "607-610", None, None, None, None, "阻力607-610，支撑没破，上个星期让买是看到有人进场"),
    ("2026-03-23T09:41:00", "$MSTR", None, None, None, None, "139", "支撑没破，往下是洗盘，过了139并站稳洗盘就结束"),
    ("2026-03-23T09:41:00", "$FIG", None, None, "21.88-22.2", None, None, "手上有fig的不动它，如果到21.88-22.2加一仓"),
    ("2026-03-23T09:54:00", "$TSLA", None, None, None, None, "382", "只要站稳382，就安全了"),
    ("2026-03-23T09:54:00", "$AMD", None, None, None, None, "210", "一定要突破210才行"),
    ("2026-03-23T10:12:00", "$HIMS", None, None, "19.98-20.3", None, None, "尽量不动，如果到19.98-20.3加一仓，也有可能到不了，有看这轮洗盘多少小散给洗下去了，无论怎么走会卖个好价钱，在盯着"),
    ("2026-03-23T10:19:00", "$MULL", None, None, None, None, None, "会找机会做，上个星期五买的进水里了，考虑到周末没说，会及时更新。买这个2倍当反弹做，到更低价格才不当反弹，因为有190以上的小散在里面，是要让小散出局的"),
    ("2026-03-23T10:19:00", "$CRCL", None, None, None, None, None, "现在是半山腰的价格，今天倒是想涨，币股还是耐心一点，看它洗到哪里"),
    ("2026-03-23T11:41:00", "$AG", None, None, None, None, "19.68", "16.88买了ag，不突破19.68减仓，到下面再接。2倍的要减仓，怕卖飞就分批减"),
    ("2026-03-23T12:03:00", "$TSLL", None, None, None, None, None, "昨天特意看了特斯拉，大趋势没破，做tsll心理就有底，还不是上量时候，等到了市场价进。大盘spx和qqq昨晚大跌都没到多空交战，多方力量没投降，多做几次有利就走"),
    ("2026-03-23T12:10:00", "$MULL", None, None, "152.9-153.38", None, None, "预设152.9-153.38，到不了改市场价"),
    ("2026-03-23T12:10:00", "$MU", None, None, None, None, None, "MU的价格会喊，这个星期不能确定能不能到"),
    ("2026-03-23T12:10:00", "$SNDK", None, None, None, None, None, "等待建仓，这个星期到不了"),
    ("2026-03-23T12:22:00", "$TSLL", None, None, None, None, None, "肯定地说，特斯拉从上个星期包括昨晚包括今天，全是严格按照机子在走，大概率会在tsll上把币股亏损夺回来"),
    ("2026-03-23T13:08:00", "$MULL", None, None, None, None, None, "炒这个mull一定要轻仓，这种半山腰价格就是做波段，等mu到了价格同时做股票和2倍"),
    ("2026-03-23T13:31:00", "$NBIL", None, None, "12", None, None, "早上减仓的，等到12左右再接回"),
    ("2026-03-23T13:31:00", "$CRCL", None, None, "116.8-118.8", None, None, "在116.8-118.8接回"),
    ("2026-03-23T13:43:00", "$ORCL", None, None, None, None, "128", "破128趋势就是跌"),
    ("2026-03-23T14:00:00", "$TSLA", None, "369", None, None, "386", "今天市场按小级别走，按照它的思路减仓。不突破386减仓tsll，接回价格按373-374接2倍（多方的价格，破了就下），不跌破369就是洗盘，跌破也无所谓，等tsll一个价格好长时间了"),
    ("2026-03-23T14:00:00", "$TSLL", None, None, None, None, None, "不突破tsla 386减仓，接回价格按tsla 373-374接2倍，分2次接回，涨跌都不怕"),
    ("2026-03-23T14:19:00", "$ORCL", None, None, None, None, None, "在进入洗盘的模式，拿好了，股票别减"),
    ("2026-03-23T14:45:00", "$QCOM", None, None, None, None, None, "好奇怪，能源量子类在悄悄涨，估计有什么消息"),
    ("2026-03-23T15:22:00", "$QCOM", None, None, None, None, None, "在做形态，如果再跌一点就可以加仓了，今天最低127.41"),
    ("2026-03-23T15:35:00", "$QUBX", None, None, None, None, "9.1", "不突破9.1，减仓"),

    # 2026-03-24
    ("2026-03-24T09:58:00", "$MULL", None, None, "144.88", None, None, "已经买了mull，预设144.88加仓，这一单设止损，如果到看到的价格会及时更新"),
    ("2026-03-24T09:58:00", "$TSLA", None, None, None, None, None, "今天大概率涨"),
    ("2026-03-24T09:58:00", "$MSFT", None, None, None, None, None, "今天是砸盘"),
    ("2026-03-24T09:58:00", "$CRCL", None, None, "111.88-112.28", None, None, "预设111.88-112.28买接回crcl，手上没有的不动"),
    ("2026-03-24T10:20:00", "$CRCL", None, "107", "102", None, None, "不慌，107有支撑不加，到102再加。遇到这种情况肯定有消息要冷静，像大石头从山上滚下来，要避开侧身看它速度慢了再冲上去。币股发生什么不知道，只说操作，买一单到水里后先不管，预设极低加仓点给它走，然后做别的"),
    ("2026-03-24T10:46:00", "$MSFL", None, None, None, None, None, "今天接回昨天减仓的msfl"),
    ("2026-03-24T13:01:00", "$METU", None, None, None, None, None, "昨天减仓的，做好准备，接回"),
    ("2026-03-24T13:01:00", "$CRCL", None, None, "92", None, "107.6", "明天反弹不突破107.6卖掉今天加的，等92再动，吸取上次教训，别频繁加仓"),
    ("2026-03-24T13:58:00", "$MSFT", None, None, None, None, None, "和meta都没有破大级别的形态"),
    ("2026-03-24T13:58:00", "$META", None, None, None, None, None, "和msft都没有破大级别的形态，Goog等"),
    ("2026-03-24T14:08:00", "$CRCL", None, None, "95-98", "107", None, "刚复盘了一下crcl，这种消息竟然按小时线走说明有人在买，立即调整策略：98、95加仓，107减仓"),
    ("2026-03-24T14:36:00", "$MULL", None, None, None, None, "151", "买到的如果不突破151就卖，突破了就拿着"),
    ("2026-03-24T15:47:00", "$HIMS", None, None, "20.98-21", "20.53", None, "预设20.98-21买hims，一直到明天收盘有效，止损20.53，发现metu 36被套的都没跑掉，不要重仓"),
    ("2026-03-24T15:47:00", "$FIG", None, "21", None, None, None, "支撑21，破了也没事，不要重仓"),

    # 2026-03-25
    ("2026-03-25T09:36:00", "$TSLA", "394-395.8", None, None, None, "395.8", "阻力394-395.8，如果突破395.8并且站稳，就挑战399"),
    ("2026-03-25T09:36:00", "$NVDA", "180", None, None, None, "184", "阻力180，突破184才转为涨"),
    ("2026-03-25T09:36:00", "$MSFT", "378-379.9", None, None, None, None, "阻力378-379.9"),
    ("2026-03-25T09:36:00", "$GOOG", None, "288", None, None, None, "昨天复盘后发现在多空交战价格上面有一个288的支撑，会经常测试，股票可以买，2倍不要买"),
    ("2026-03-25T09:36:00", "$AMD", None, None, None, None, "220", "还没有突破，站稳220，底仓和股票都不要卖"),
    ("2026-03-25T09:36:00", "$AMDL", None, None, None, None, "220", "2倍amdl不突破AMD 220减仓，但底仓和股票都不要卖"),
    ("2026-03-25T09:48:00", "$META", "603.8", None, None, None, "610", "阻力603.8，耐心等待突破610，今天可能到不了"),
    ("2026-03-25T09:48:00", "$MSTR", "143.8-147", None, None, None, None, "前几天都在洗盘为了更高价格，今天阻力143.8-147"),
    ("2026-03-25T09:48:00", "$LAC", "4.2", None, None, None, "4.5", "今天阻力4.2，不突破4.5会来回折腾"),
    ("2026-03-25T09:48:00", "$DELL", None, None, None, None, "182", "已经突破182，仍然没打算卖，股票尽量别频繁操作，如果手痒就做2倍或那天启动的股票"),
    ("2026-03-25T09:55:00", "$CRCL", None, None, None, None, "111", "昨天看来是有人死坏，不突破111减仓"),
    ("2026-03-25T09:55:00", "$MU", None, None, None, None, None, "专门说一下，昨天不知道151有没有走，做好加仓的准备，快到建仓的价格了"),
    ("2026-03-25T09:55:00", "$MULL", None, None, "130.28-132.88", None, None, "谁手上还有mull？现在开始加仓2次，第一次132.88，第二次130.28，到不了改市场价"),
    ("2026-03-25T09:55:00", "$GOOG", None, None, None, None, None, "自己认为还有好价格，但股市是走出来的，认为回调没有结束，不建议买2倍，股票建仓轻仓"),
    ("2026-03-25T10:03:00", "$MULL", None, None, "130.28", None, None, "为什么这么近？心里有数，抢反弹，可以就预设130.28，然后不到就市场价倒追"),
    ("2026-03-25T11:22:00", "$MSFL", None, None, "15-15.18", None, None, "预设15-15.18加msfl"),
    ("2026-03-25T11:22:00", "$ORCL", None, None, None, None, None, "预设加一单orcl，另外一单等待"),
    ("2026-03-25T12:03:00", "$MULL", None, None, None, None, None, "132.88 mull谁买到了？之所以这么近距离加仓，就是因为多空今天交战"),
    ("2026-03-25T12:03:00", "$TSLL", None, None, None, None, None, "减仓的等待收盘前看有没有机会接回来"),
    ("2026-03-25T12:03:00", "$AMDL", None, None, None, None, None, "减仓的今天不再动，等明后2天"),
    ("2026-03-25T13:18:00", "$MSFT", None, None, None, None, None, "回调没结束，快了"),
    ("2026-03-25T13:18:00", "$SOXL", None, None, None, None, None, "行情没走完"),
    ("2026-03-25T13:31:00", "$META", None, None, None, None, None, "走的不错，减仓了吗？"),
    ("2026-03-25T13:43:00", "$AMD", None, None, None, None, None, "比较有想法，走上了边洗边拉的模式，前几天一直在盯着多空交战"),
    ("2026-03-25T13:43:00", "$CRCL", None, None, None, None, None, "没走掉的不要慌，既然有买方昨天进场，它再洗就给它洗"),
    ("2026-03-25T14:00:00", "$VCX", None, None, None, None, None, "看着它发疯，跳进去一次立即走了，太疯了，竟然在330洗过一次，这个股一定会套小散"),
    ("2026-03-25T14:33:00", "$META", "603.8", None, None, None, None, "今天603.8没突破，最高603.62，做好再洗一次的准备"),
    ("2026-03-25T14:58:00", "$TSLL", None, "13", "12.88-13.15", None, None, "早上都减仓了吗，13是支撑，预设12.88-13.15接回一半，防止再洗"),
    ("2026-03-25T15:37:00", "$ORCL", None, None, None, None, None, "少买一点，今天破了一次"),

    # 2026-03-27
    ("2026-03-27T09:33:00", "$TSLL", None, None, "11.38", None, None, "做为操作重点，不是说特斯拉有多好，是因为放在观察仓第一个，只要复盘都会先看它已很熟悉。预设11.38加仓tsll，特斯拉大概率今天是砸盘"),
    ("2026-03-27T09:33:00", "$NVDA", None, None, None, None, "176", "昨天没提操作是在等一个空头点位，多方的176回不来就等"),
    ("2026-03-27T09:33:00", "$MSFT", None, "358", None, None, None, "支撑358"),
    ("2026-03-27T09:33:00", "$AMD", None, "199", "193", None, None, "支撑199，破了也没事，到193再加"),
    ("2026-03-27T09:33:00", "$META", None, "533", None, None, None, "支撑533"),
    ("2026-03-27T09:40:00", "$METU", None, None, "19.72-19.8", "19.47", None, "预设19.72-19.8加一仓，设止损19.47"),
    ("2026-03-27T09:40:00", "$MSTR", None, "126.8-127.7", None, None, None, "支撑126.8-127.7，大盘破了一次，只有站稳6429"),
    ("2026-03-27T09:40:00", "$HIMS", None, None, None, None, None, "不知道为什么今天要砸盘，以前说过回调到19块多"),
    ("2026-03-27T09:40:00", "$ORCL", None, None, None, None, None, "仍然没到上量的时候，还差几块钱"),
    ("2026-03-27T09:40:00", "$CRCL", None, "92", None, None, None, "支撑92"),
    ("2026-03-27T09:40:00", "$MULL", None, None, None, None, None, "有利分批卖"),
    ("2026-03-27T10:00:00", "$META", None, None, None, None, None, "今天是生死战，在盯着"),
    ("2026-03-27T10:00:00", "$VST", None, None, None, None, None, "一直要喊vst，降不下来，等，会等来好价格"),
    ("2026-03-27T10:08:00", "$VST", None, None, None, None, None, "是好股，底仓也在"),
    ("2026-03-27T10:33:00", "$METU", None, None, None, None, None, "还没有到多空交战，不要慌，空方还没拿下来，等待"),
    ("2026-03-27T11:16:00", "$NVDA", None, None, "166.88", None, None, "谁手上还有钱？预设166.88买一点nvda"),
    ("2026-03-27T11:16:00", "$AMDL", None, None, "10.92-11.28", None, None, "预设10.92-11.28买amdl"),
    ("2026-03-27T11:40:00", "$METU", None, None, None, None, None, "无论怎么走，哪怕破19，未来几天大概率要回到20以上"),
    ("2026-03-27T11:40:00", "$AMZU", None, None, "24.68", None, None, "预设24.68买amzu，到不了就算了"),
    ("2026-03-27T12:36:00", "$ORCX", None, None, None, "24.88", None, "好奇怪，看orcx最高24.87，为什么预设的24.88成交了？谁这么任性买了我卖的"),
    ("2026-03-27T12:44:00", "$QCOM", None, None, None, None, None, "看下个星期有没有机会，没到就等"),
    ("2026-03-27T13:00:00", "$QQQ", None, "565.5", None, None, None, "有支撑565.5，今天基本决定未来两个星期走势，spy多空交战到了"),
    ("2026-03-27T13:00:00", "$TQQQ", None, None, "564.8", None, None, "到qqq 564.8买一单tqqq，设止损，如果收盘前能到就买，今天一定要有耐心，留钱"),
    ("2026-03-27T13:00:00", "$AVGO", None, None, None, None, None, "下个星期买，我来喊"),
    ("2026-03-27T13:41:00", "$AMZN", None, None, None, None, None, "等待，等2个月了，再等一等"),
    ("2026-03-27T14:15:00", "$META", None, "517-519", None, None, None, "在等meta的空头，股票还有新低，但是今天517-519是极限"),
    ("2026-03-27T14:36:00", "$QQQ", None, None, None, None, "561", "不破561就买"),
    ("2026-03-27T14:36:00", "$CWVX", None, None, "17.58", None, None, "17.58买的cwvx，把止损往上提，严格说是止盈，处在股市快到悬崖边的状态，冷静就能活下来"),
    ("2026-03-27T15:44:00", "$HIMS", None, None, None, None, None, "今天hims和himz可以同时买，设止损，20%概率再跌，meta空头没拿下来"),
    ("2026-03-27T15:44:00", "$HIMZ", None, None, None, None, None, "今天hims和himz可以同时买，设止损，20%概率再跌"),
    ("2026-03-27T15:55:00", "$TSM", None, None, "321.98", None, None, "预设321.98，从来对大多数都跌的股市不是担心，最担心小股票被操纵"),
]
