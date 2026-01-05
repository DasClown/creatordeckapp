import streamlit as st
import pandas as pd

def render_planner(supabase):
    st.title("📅 CONTENT PLANNER")

    res = supabase.table("content_plan").select("*").execute()
    df_plan = pd.DataFrame(res.data)

    # Quick Add Form
    with st.expander("➕ ADD NEW CONTENT"):
        with st.form("planner_form"):
            date = st.date_input("Date")
            platform = st.selectbox("Platform", ["Instagram", "YouTube", "TikTok"])
            c_type = st.selectbox("Type", ["Reel", "Video", "Post", "Story"])
            title = st.text_input("Title/Hook")
            
            # Asset Linking aus Gallery
            try:
                files = supabase.storage.from_("assets").list("branded")
                file_options = [f['name'] for f in files] if files else []
                selected_asset = st.selectbox("Link Asset", ["None"] + file_options)
            except:
                selected_asset = "None"
                st.caption("⚠️ Gallery Assets nicht verfügbar")
            
            if st.form_submit_button("Schedule"):
                asset_url = None
                if selected_asset != "None":
                    asset_url = supabase.storage.from_("assets").get_public_url(f"branded/{selected_asset}")
                
                supabase.table("content_plan").insert({
                    "publish_date": str(date), 
                    "platform": platform, 
                    "content_type": c_type, 
                    "title": title,
                    "asset_url": asset_url
                }).execute()
                st.rerun()

    if not df_plan.empty:
        st.subheader("Upcoming Schedule")
        st.dataframe(df_plan.sort_values("publish_date"), use_container_width=True, hide_index=True)
