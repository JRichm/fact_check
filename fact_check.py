# James Richmond

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

from dateutil.relativedelta import relativedelta


def open_presidents(filename):
    presidents = pd.read_csv(filename)
    for col in ['term_start', 'term_end']:
        presidents[col] = pd.to_datetime(presidents[col], format="%Y%m%d").apply(lambda x: x.date() if pd.notna(x) else None)
    presidents['party'] = presidents['party'].apply(lambda x: x.lower().strip())
    presidents = presidents[["name", "term_start", "term_end", "party"]]
    presidents_filtered = presidents[
        (presidents['term_end'].notna()) &
        (presidents['term_start'] >= dt.date(1950, 1, 1))

    ]

    return presidents


def open_jobs(filename):
    jobs = pd.read_csv(filename)
    monthly_jobs = {}
    for index, row in jobs.iterrows():
        for x in range(1, 13):
            date = dt.date(int(row['Year']), x, 1)
            month = date.strftime("%b")
            num_jobs = row[month]

            try:
                monthly_jobs[date] = int(num_jobs) * 1000
            except:
                pass

    return monthly_jobs



def get_graph_highlighting_parties(jobs, presidents):
    figure = plt.figure(figsize=(25,8))
    axes = figure.add_subplot()

    axes.set_title(f"Total Jobs with Presidential Party ({next(iter(jobs.keys())).year}-{next(iter(reversed(jobs.keys()))).year})", fontsize=14, fontweight='bold')
    axes.plot(jobs.keys(), jobs.values())

    color_map = color_map = {"democratic": "blue", "republican": "red"}
    party_changes = []
    for index, row in presidents.iterrows():

        term_start = row['term_start']
        term_end = row['term_end']
        party = row['party']

        for x in [term_start, term_end]:
            if pd.isna(x) or isinstance(x, type(pd.NaT)):
                continue


        if index == 0 or (len(party_changes) > 0 and party != party_changes[-1][1]):
            party_changes.append((term_start, party))

        if party in color_map:
            color = color_map[party]
            axes.axvspan(term_start, term_end, alpha=0.15, color=color)

    return figure


def highlight_period(monthly_jobs, figure, dates):

    dates_to_highlight = {
        k: v for k, v in monthly_jobs.items()
        if dates[0] <= k <= dates[1]
    }

    axes = figure.get_axes()[0]
    axes.plot(dates_to_highlight.keys(), dates_to_highlight.values(), linewidth=3, color='red')
    
    first_key = next(iter(dates_to_highlight))
    last_key = next(reversed(dates_to_highlight))
        
    axes.scatter(
        [first_key, last_key],
        [dates_to_highlight.get(first_key), dates_to_highlight.get(last_key)],
        color="red",
        s=150,
        zorder=5
    )

    axes.annotate(
        f"{first_key.strftime('%m/%d/%Y')}\n{dates_to_highlight.get(first_key) / 1_000_000:<.1f}m jobs",
        xy=(first_key, dates_to_highlight.get(first_key)),
        xytext=(10, -40),
        textcoords='offset points',
        fontsize=14
    )

    axes.annotate(
        f"{last_key.strftime('%m/%d/%Y')}\n{dates_to_highlight.get(last_key) / 1_000_000:<.1f}m jobs",
        xy=(last_key, dates_to_highlight.get(last_key)),
        xytext=(10, -40),
        textcoords='offset points',
        fontsize=14
    )

    jobs_created = dates_to_highlight.get(last_key) - dates_to_highlight.get(first_key)
    
    axes.set_title(f"Total Jobs Created (Highlighting {dates[0].year}-{dates[1].year})", fontsize=14, fontweight='bold')

    axes.text(
        0.75,
        0.05, 
        f'Jobs created: {jobs_created/1_000_000:.1f}m',
        transform=plt.gca().transAxes,
        fontsize=20,
        bbox={"color": "gray", "alpha": 0.5}
    )

    return figure

# graph_1 = get_graph_highlighting_parties(monthly_jobs, presidents_filtered)
# graph_2 = highlight_period(graph_1, (dt.date(1961, 9, 1), dt.date(2012, 9, 1)))


def find_party_job_growth(president_df, monthly_jobs, dates):
    # filter presidents df to presidents that have an end date after dates[0] and start date before dates[0]
    pres_s = president_df.copy()[
        (president_df['term_end'] >= dates[0]) &
        (president_df['term_start'] <= dates[1])
    ].sort_values(by="term_start").reset_index(drop=True)
    
    pres_s['term_start_fix'] = pres_s['term_start'].apply(
        lambda x: dt.date(x.year, x.month, 1) if x.day < 15 
        else dt.date(x.year, x.month, 1) + relativedelta(months=1)
    )

    pres_s['term_end_fix'] = pres_s['term_end'].apply(
        lambda x: dt.date(x.year, x.month, 1) if x.day < 15 
        else dt.date(x.year, x.month, 1) + relativedelta(months=1)
    )

    start_search = pres_s[
        (pres_s["term_start"] <= dates[0]) &
        (pres_s["term_end"] >= dates[0])    
    ]

    if start_search.empty or len(start_search) > 1:
        raise ValueError("Something went wrong when changing first president's term start fix")
    else:
        pres_s.loc[start_search.index[0], 'term_start_fix'] = dates[0]

    # fix the last presidents end date
    end_search = pres_s[
        (pres_s["term_start"] <= dates[1]) &
        (pres_s["term_end"] >= dates[1])    
    ]

    if end_search.empty or len(end_search) > 1:
        raise ValueError("Something went wrong when changing last president's term end fix")
    else:
        pres_s.loc[end_search.index[0], 'term_end_fix'] = dates[1]



    pres_s['jobs_at_start'] = pres_s['term_start_fix'].apply(lambda x: monthly_jobs.get(x))
    pres_s['jobs_at_end'] = pres_s['term_end_fix'].apply(lambda x: monthly_jobs.get(x))

    pres_s['jobs_growth'] = pres_s.apply(lambda row: row['jobs_at_end'] - row['jobs_at_start'], axis=1)


    # display(pres_s[['name', 'term_start_fix', 'term_end_fix', 'jobs_at_start', 'jobs_at_end', "jobs_growth", 'party']])
    
    party_growth = {
        "republican": 0,
        "democratic": 0
    }
    for index, row in pres_s.iterrows():
        party_growth[row['party']] += row['jobs_growth']

    return party_growth


def graph_party_jobs(party_jobs):
    figure = plt.figure(figsize=(10, 8))
    axes = figure.add_subplot(111)

    parties = ['Democrats', 'Republicans']
    
    # divide nubmer of jobs by the millions
    job_millions = [
        party_jobs['democratic']/1_000_000, 
        party_jobs['republican']/1_000_000
    ]

    # bar chart for each party's job numbers
    bars = axes.bar(
        parties,
        job_millions,
        color=['blue', 'red'],
    )

    # plot lables for each bar
    for i, (bar, value) in enumerate(zip(bars, job_millions)):
        height = bar.get_height()
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{value:.1f}M',
            ha='center',
            va='bottom',
        )
    
    axes.set_ylabel('Jobs Created (millions)', fontsize=12)
    axes.set_title('Jobs Created by Party', fontsize=14, fontweight='bold')
    axes.grid(True, axis='y', alpha=0.3)

    return figure


def graph_validate_score(party_jobs):
    figure = plt.figure(figsize=(10, 8))
    axes = figure.add_subplot(111)

    x = np.arange(2)
    width = 0.35
    
    clinton_claim = [42, 24]
    actual_values = [
        party_jobs['democratic'] / 1_000_000,
        party_jobs['republican'] / 1_000_000
    ]
    
    bars1 = plt.bar(
        x - width/2,
        clinton_claim,
        width,
        label='Clinton\'s Claim',
        color=['blue', 'red'],
        alpha=0.4,
    )
    
    bars2 = plt.bar(
        x + width / 2,
        actual_values,
        width,
        label='Actual Data',
        color=['blue', 'red'],
        alpha=0.8,
    )
    
    axes.set_ylabel('Jobs Created (millions)', fontsize=12)
    axes.set_title("Clinton's Claim vs Actual Data (1961-2012)", fontsize=14, fontweight='bold')
    axes.set_xticks(x, ['Democrats', 'Republicans'])
    axes.legend(fontsize=12)
    axes.grid(True, axis='y', alpha=0.3)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.1f}M',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )

    return figure


if __name__ == "__main__":
    presidents_csv = "presidents.txt"
    jobs_csv = "BLS_private.csv"

    presidents_df = open_presidents(presidents_csv)
    monthly_jobs = open_jobs(jobs_csv)

    start_date = dt.date(1961, 9, 1)
    end_date = dt.date(2012, 9, 1)

    ps_to_show = presidents_df[
        (presidents_df['term_end'] >= start_date) &
        (presidents_df['term_start'] <= end_date)
    ]

    party_growth = find_party_job_growth(presidents_df, monthly_jobs, (start_date, end_date))

    graph_1 = get_graph_highlighting_parties(monthly_jobs, ps_to_show)
    graph_1.savefig('graph_1.png', dpi=300, bbox_inches='tight')

    graph_2 = highlight_period(monthly_jobs, graph_1, (dt.date(1961, 9, 1), dt.date(2012, 9, 1)))
    graph_2.savefig('graph_2.png', dpi=300, bbox_inches='tight')

    graph_3 = graph_party_jobs(party_growth)
    graph_3.savefig('graph_3.png', dpi=300, bbox_inches='tight')

    graph_4 = graph_validate_score(party_growth)
    graph_4.savefig('graph_4.png', dpi=300, bbox_inches='tight')