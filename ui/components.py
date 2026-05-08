import html
import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

    .chip-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 6px;
        margin-bottom: 14px;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 5px 9px;
        border: 1px solid rgba(250,250,250,.14);
        border-radius: 999px;
        background: rgba(255,255,255,.045);
        font-size: .88rem;
        line-height: 1;
        white-space: nowrap;
    }

    .chip img {
        width: 24px;
        height: 24px;
        object-fit: cover;
    }

    .result-card {
        border: 1px solid rgba(250,250,250,.12);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 8px;
        background: rgba(255,255,255,.035);
    }

    .small-muted {
        color: rgba(250,250,250,.65);
        font-size: .82rem;
    }

    .item-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 10px;
        margin-top: 8px;
    }

    .item-card {
        display: flex;
        align-items: center;
        gap: 12px;
        border: 1px solid rgba(250,250,250,.12);
        border-radius: 12px;
        padding: 10px 12px;
        background: rgba(255,255,255,.035);
    }

    .champ-area {
        min-width: 95px;
    }

    .item-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
    }

    .item-icon {
        width: 32px;
        height: 32px;
        object-fit: cover;
        border-radius: 6px;
        border: 1px solid rgba(250,250,250,.16);
        background: rgba(255,255,255,.04);
    }
    </style>
""", unsafe_allow_html=True)


def asset(assets, group, name):
    return assets.get(group, {}).get(name, "")


def chip(name, icon_url="", kind="champion", extra=""):
    safe_name = html.escape(str(name))
    safe_extra = html.escape(str(extra)) if extra else ""

    radius = "0px" if kind == "trait" else "6px"
    img = f'<img src="{icon_url}" style="border-radius:{radius}">' if icon_url else ""
    extra_html = f"<span class='muted'>{safe_extra}</span>" if safe_extra else ""

    return f"<span class='chip'>{img}<b>{safe_name}</b>{extra_html}</span>"


def render_chip_grid(items):
    if not items:
        return

    st.markdown(
        "<div class='chip-grid'>" + "".join(items) + "</div>",
        unsafe_allow_html=True
    )


def item_icon(icon_url):
    if not icon_url:
        return ""

    return f'<img src="{icon_url}" class="item-icon">'


def show_selected_champions(selected_champions, assets):
    if not selected_champions:
        st.info("Select champions to see your board.")
        return

    render_chip_grid([
        chip(champ, asset(assets, "champions", champ))
        for champ in selected_champions
    ])


def show_board_traits(trait_counts, assets):
    if not trait_counts:
        st.info("No traits detected.")
        return

    render_chip_grid([
        chip(
            name=trait,
            icon_url=asset(assets, "traits", trait),
            kind="trait",
            extra=f"x{count}"
        )
        for trait, count in sorted(trait_counts.items(), key=lambda x: (-x[1], x[0]))
    ])


def show_item_recommendations(selected_champions, item_recs, assets):
    cards = []

    for champ in selected_champions:
        item_icons = [
            item_icon(asset(assets, "items", item))
            for item, _ in item_recs.get(champ, [])
            if asset(assets, "items", item)
        ]

        if not item_icons:
            continue

        champ_chip = chip(champ, asset(assets, "champions", champ))

        cards.append(
            "<div class='item-card'>"
            f"<div class='champ-area'>{champ_chip}</div>"
            f"<div class='item-row'>{''.join(item_icons)}</div>"
            "</div>"
        )

    if not cards:
        st.info("No item recommendations found for selected champions yet.")
        return

    st.markdown(
        "<div class='item-grid'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True
    )


def show_top_traits(trait_rates, assets, limit=3):
    top_traits = list(trait_rates.items())[:limit]

    for trait, stats in top_traits:
        trait_chip = chip(
            name=trait,
            icon_url=asset(assets, "traits", trait),
            kind="trait"
        )

        st.markdown(
            "<div class='card'>"
            f"{trait_chip}<br>"
            f"<span class='muted'>{stats['top4_rate']:.1%} top4 rate · "
            f"avg placement {stats['avg_placement']:.1f} · "
            f"n={stats['count']}</span>"
            "</div>",
            unsafe_allow_html=True
        )

    return top_traits