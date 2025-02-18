import numpy as np
import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="veroXis Pricing Model Tool",
    page_icon="💰",
    layout="wide"
)

# Custom CSS to improve the UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .pricing-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def calculate_channel_effectiveness():
    """
    Calculate channel effectiveness based on industry standards
    Returns a dict with channel weights and recommended allocations
    """
    return {
        'sms': {
            'weight': 0.15,  # Lowest impact due to no links
            'min_allocation': 0,
            'max_allocation': 100,
            'engagement_rate': 0.05,  # 5% engagement rate
            'recommended': 20
        },
        'app': {
            'weight': 0.25,  # Better than SMS due to direct interaction
            'min_allocation': 0,
            'max_allocation': 100,
            'engagement_rate': 0.15,  # 15% engagement rate
            'recommended': 30
        },
        'edm': {
            'weight': 0.20,  # Good for detailed content
            'min_allocation': 0,
            'max_allocation': 100,
            'engagement_rate': 0.08,  # 8% click rate
            'recommended': 25
        },
        'statement': {
            'weight': 0.40,  # Highest impact
            'engagement_rate': 0.35,  # 35% open rate
            'min_weeks': 0,
            'recommended_weeks': 4
        },
        'banner': {
            'weight': 0.10,  # Supplementary channel
            'engagement_rate': 0.02,  # 2% click rate
            'min_weeks': 0,
            'recommended_weeks': 3
        }
    }


def adjust_channel_costs(target_users, base_sms, base_app, base_edm, base_statement, base_banner):
    """Adjusts channel costs based on target user bands."""
    if target_users <= 100000:
        return base_sms, base_app, base_edm, base_statement, base_banner
    elif target_users <= 200000:
        return (base_sms * 0.90, base_app * 0.90, base_edm * 0.90,
                base_statement * 0.95, base_banner * 0.80)
    else:
        return (base_sms * 0.85, base_app * 0.85, base_edm * 0.85,
                base_statement * 0.95, base_banner * 0.75)


def calculate_cpa(target_users, total_cost_per_user, base_approval_rate, diminishing_factor, setup_cost, channel_allocations, channel_metrics):
    """
    Calculates the CPA based on weighted channel effectiveness

    Parameters:
    - channel_allocations: Dict with percentages for each channel
    - channel_metrics: Dict with engagement rates and weights for each channel
    """
    marketing_cost = (total_cost_per_user * target_users) + setup_cost

    # Calculate weighted effectiveness
    total_effectiveness = 0
    for channel, allocation in channel_allocations.items():
        if channel in ['sms', 'app', 'edm']:
            effectiveness = (
                allocation/100 *
                channel_metrics[channel]['weight'] *
                channel_metrics[channel]['engagement_rate']
            )
            total_effectiveness += effectiveness

    # Add statement and banner impact
    statement_impact = channel_metrics['statement']['weight'] * \
        channel_metrics['statement']['engagement_rate']
    banner_impact = channel_metrics['banner']['weight'] * \
        channel_metrics['banner']['engagement_rate']
    total_effectiveness += (statement_impact + banner_impact)

    # Calculate adjusted approval rate
    adjusted_approval_rate = base_approval_rate * total_effectiveness

    # Calculate approvals
    num_approvals = target_users * adjusted_approval_rate * diminishing_factor
    cpa = marketing_cost / num_approvals if num_approvals > 0 else 0

    return marketing_cost, num_approvals, cpa, adjusted_approval_rate, total_effectiveness


def main():
    # Header with company logo/name
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <h1 style='text-align: center'>
                🎯 vero<span style='color: red; font-weight: bold;'>X</span>is Pricing Model Tool
            </h1>
        """, unsafe_allow_html=True)
        st.markdown("---")

    # Create two main columns for the layout
    left_col, right_col = st.columns([2, 3])

    with left_col:
        st.subheader("📊 Campaign Parameters")
        with st.expander("Target Audience", expanded=True):
            target_users = st.slider(
                "Target User Base",
                50000, 500000, 200000, 10000,
                help="Select the number of users you want to target"
            )

            # Conversion Rate Guide
            st.info("""
            **Industry Conversion Rate Benchmarks:**
            • Financial Services: 2.5% - 5.5%
            • Consumer Banking: 2.9% - 6.1%
            • Credit Cards: 1.8% - 4.7%
            • Personal Loans: 2.2% - 5.9%
            • Investment Products: 1.5% - 3.8%
            • Insurance: 2.4% - 4.9%
            """)

            base_approval_rate = st.number_input(
                "Expected Base Conversion Rate (%)",
                min_value=0.1,
                max_value=15.0,  # Limited to realistic maximum
                value=5.49,
                step=0.01,
                help="Your expected conversion rate based on historical data or campaign objectives"
            ) / 100

            # Validation for conversion rate
            if base_approval_rate > 0.08:  # Over 8%
                st.warning("""
                ⚠️ Your expected conversion rate is higher than typical industry standards.
                Please ensure you have historical data to support this projection.
                """)
            elif base_approval_rate < 0.01:  # Under 1%
                st.warning("""
                ⚠️ Your expected conversion rate is lower than typical industry standards.
                Consider:
                • Reviewing your target audience selection
                • Enhancing your campaign messaging
                • Optimizing channel mix for better conversion
                """)

        # Get channel metrics
        channel_metrics = calculate_channel_effectiveness()

        st.markdown("### 📱 Channel Allocation")
        st.info("""
            **Channel Impact Guide:**
            • Statement Messages: 35% open rate - Highest engagement
            • App Notifications: 15% engagement rate - Good for direct interaction
            • eDM: 8% click rate - Effective for detailed content
            • SMS: 5% engagement rate - Limited by no-link policy
            • Website Banner: 2% click rate - Supplementary reach
        """)

        # Channel allocation with real-time validation
        col1, col2 = st.columns(2)
        with col1:
            sms_pct = st.slider("SMS Reach (%)",
                                min_value=channel_metrics['sms']['min_allocation'],
                                max_value=channel_metrics['sms']['max_allocation'],
                                value=channel_metrics['sms']['recommended'],
                                help=f"Recommended: {channel_metrics['sms']['recommended']}% (Limited impact due to no links)")

            edm_pct = st.slider("eDM Reach (%)",
                                min_value=channel_metrics['edm']['min_allocation'],
                                max_value=channel_metrics['edm']['max_allocation'],
                                value=channel_metrics['edm']['recommended'],
                                help=f"Recommended: {channel_metrics['edm']['recommended']}% (Good for detailed content)")

            app_pct = st.slider("App Notification (%)",
                                min_value=channel_metrics['app']['min_allocation'],
                                max_value=channel_metrics['app']['max_allocation'],
                                value=channel_metrics['app']['recommended'],
                                help=f"Recommended: {channel_metrics['app']['recommended']}% (Direct interaction)")

            # Calculate total reach
            total_reach = sms_pct + edm_pct + app_pct

            # Display reach status
            st.markdown("#### Channel Mix Effectiveness")
            if total_reach > 100:
                st.error(
                    f"⚠️ Total reach ({total_reach}%) exceeds 100%. Please adjust your allocation.")
            elif total_reach < 100:
                remaining = 100 - total_reach
                effectiveness_impact = total_reach/100
                st.warning(f"""
                ⚠️ Current reach is {total_reach}%. Unused allocation: {remaining}%
                
                Impact: Your campaign effectiveness will be reduced to {effectiveness_impact:.1%} of maximum potential.
                Consider:
                • Increasing allocation to existing channels
                • Adding unused channels to increase reach
                • Or continue with reduced reach if targeting specific segments
                """)
            else:
                st.success(
                    "✅ Perfect! You are reaching 100% of your target audience.")

            # Calculate channel mix effectiveness
            channel_allocations = {
                'sms': sms_pct,
                'app': app_pct,
                'edm': edm_pct
            }

        with col2:
            weeks_statement = st.slider("Statement Message (Weeks)",
                                        min_value=channel_metrics['statement']['min_weeks'],
                                        max_value=12,
                                        value=channel_metrics['statement']['recommended_weeks'],
                                        help="Recommended: 4 weeks (Highest engagement channel)")

            weeks_banner = st.slider("Website Banner (Weeks)",
                                     min_value=channel_metrics['banner']['min_weeks'],
                                     max_value=12,
                                     value=channel_metrics['banner']['recommended_weeks'],
                                     help="Recommended: 3 weeks (Supplementary channel)")

        # Setup Cost Display
        st.markdown("### 💰 Setup Cost")
        setup_cost = 10000
        st.metric("Fixed Setup Fee", f"RM {setup_cost:,.2f}")

    # Calculate base costs
    base_sms_cost = 0.03
    base_app_notif_cost = 0.06
    base_edm_cost = 0.20
    base_statement_cost = 4000 * weeks_statement
    base_banner_cost = 750 * weeks_banner

    # Adjust costs based on volume
    sms_cost, app_notif_cost, edm_cost, statement_cost, banner_cost = adjust_channel_costs(
        target_users, base_sms_cost, base_app_notif_cost, base_edm_cost,
        base_statement_cost, base_banner_cost
    )

    # Calculate total cost per user
    total_cost_per_user = (
        (sms_cost * sms_pct / 100) +
        (app_notif_cost * app_pct / 100) +
        (edm_cost * edm_pct / 100) +
        (statement_cost / target_users) +
        (banner_cost / target_users)
    )

    # Base approval rate and diminishing factor
    base_approval_rate = 5.49 / 100  # 5.49% base conversion rate
    diminishing_factor = np.interp(target_users, [50000, 500000], [0.5, 1.0])

    # Calculate final metrics
    marketing_cost, num_approvals, cpa, adjusted_approval_rate, total_effectiveness = calculate_cpa(
        target_users, total_cost_per_user, base_approval_rate, diminishing_factor,
        setup_cost, channel_allocations, channel_metrics
    )

    # Right column - Results Display
    with right_col:
        st.subheader("📈 Campaign Metrics")

        # Key Metrics in Cards
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Total Marketing Cost", f"RM {marketing_cost:,.2f}")
        with metrics_col2:
            st.metric("Estimated Approvals", f"{int(num_approvals):,}")
        with metrics_col3:
            st.metric("Cost Per Acquisition", f"RM {cpa:.2f}")

        # Channel Cost Breakdown
        st.markdown("### 📊 Channel Cost Breakdown")
        cost_data = {
            "Channel": ["SMS", "App Notification", "eDM", "Statement Message", "Website Banner"],
            "Cost": [
                f"RM {sms_cost:.4f}/user",
                f"RM {app_notif_cost:.4f}/user",
                f"RM {edm_cost:.4f}/user",
                f"RM {statement_cost:.2f}/week",
                f"RM {banner_cost:.2f}/week"
            ],
            "Reach/Duration": [
                f"{sms_pct}% of users",
                f"{app_pct}% of users",
                f"{edm_pct}% of users",
                f"{weeks_statement} weeks",
                f"{weeks_banner} weeks"
            ],
            "Expected Impact": [
                f"{channel_metrics['sms']['engagement_rate']*100:.1f}% engagement",
                f"{channel_metrics['app']['engagement_rate']*100:.1f}% engagement",
                f"{channel_metrics['edm']['engagement_rate']*100:.1f}% click rate",
                f"{channel_metrics['statement']['engagement_rate']*100:.1f}% open rate",
                f"{channel_metrics['banner']['engagement_rate']*100:.1f}% click rate"
            ]
        }
        st.table(pd.DataFrame(cost_data))

        # Campaign Insights
        st.markdown("### 🔍 Campaign Insights")
        st.info(f"""
        • Current target reach: {target_users:,} users
        • Channel reach utilization: {total_reach}%
        • Average cost per user: RM {total_cost_per_user:.4f}
        • Base conversion rate: {base_approval_rate*100:.2f}%
        • Adjusted conversion rate: {adjusted_approval_rate*100:.4f}%
        • Total effectiveness score: {total_effectiveness:.4f}
        • Diminishing factor applied: {diminishing_factor:.2f}
        """)

        # Action Buttons Container
        st.markdown("### 🎯 Actions")
        col1, col2 = st.columns(2)

        with col1:
            # Generate detailed report CSV
            report_data = {
                "Category": [
                    "Campaign Information", "", "", "",
                    "Channel Allocation", "", "", "", "",
                    "Costs", "", "", "", "",
                    "Campaign Metrics", "", "", "", ""
                ],
                "Item": [
                    "Target Users", "Campaign Date", "Setup Cost", "Partner Reference",
                    "SMS Reach", "eDM Reach", "App Notification", "Statement Message Duration", "Website Banner Duration",
                    "SMS Cost (per user)", "App Notification Cost (per user)", "eDM Cost (per user)", "Statement Message Cost (per week)", "Website Banner Cost (per week)",
                    "Total Marketing Cost", "Cost Per User", "Estimated Approvals", "Base Conversion Rate", "Adjusted Conversion Rate"
                ],
                "Value": [
                    f"{target_users:,}", pd.Timestamp.now().strftime(
                        '%Y-%m-%d'), f"RM {setup_cost:,.2f}", "VX" + pd.Timestamp.now().strftime('%Y%m%d%H%M'),
                    f"{sms_pct}%", f"{edm_pct}%", f"{app_pct}%", f"{weeks_statement} weeks", f"{weeks_banner} weeks",
                    f"RM {sms_cost:.4f}", f"RM {app_notif_cost:.4f}", f"RM {edm_cost:.4f}", f"RM {statement_cost:,.2f}", f"RM {banner_cost:,.2f}",
                    f"RM {marketing_cost:,.2f}", f"RM {total_cost_per_user:.4f}", f"{int(num_approvals):,}", f"{base_approval_rate*100:.2f}%", f"{adjusted_approval_rate*100:.4f}%"
                ]
            }

            st.download_button(
                label="📥 Download Campaign Report",
                data=pd.DataFrame(report_data).to_csv(index=False),
                file_name=f"veroXis_campaign_proposal_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col2:
            # Generate formal proposal/invoice CSV
            invoice_items = [
                {
                    "Item Reference": f"VX{pd.Timestamp.now().strftime('%Y%m%d%H%M')}",
                    "Date": pd.Timestamp.now().strftime('%Y-%m-%d'),
                    "Description": "Campaign Setup Fee",
                    "Quantity": "1",
                    "Unit Cost (RM)": f"{setup_cost:.2f}",
                    "Total Cost (RM)": f"{setup_cost:.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "SMS Marketing",
                    "Quantity": f"{(sms_pct/100 * target_users):,.0f}",
                    "Unit Cost (RM)": f"{sms_cost:.4f}",
                    "Total Cost (RM)": f"{(sms_cost * sms_pct/100 * target_users):.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "App Notifications",
                    "Quantity": f"{(app_pct/100 * target_users):,.0f}",
                    "Unit Cost (RM)": f"{app_notif_cost:.4f}",
                    "Total Cost (RM)": f"{(app_notif_cost * app_pct/100 * target_users):.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "eDM Campaign",
                    "Quantity": f"{(edm_pct/100 * target_users):,.0f}",
                    "Unit Cost (RM)": f"{edm_cost:.4f}",
                    "Total Cost (RM)": f"{(edm_cost * edm_pct/100 * target_users):.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "Statement Messages",
                    "Quantity": f"{weeks_statement}",
                    "Unit Cost (RM)": f"{statement_cost:.2f}",
                    "Total Cost (RM)": f"{(statement_cost * weeks_statement):.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "Website Banner",
                    "Quantity": f"{weeks_banner}",
                    "Unit Cost (RM)": f"{banner_cost:.2f}",
                    "Total Cost (RM)": f"{(banner_cost * weeks_banner):.2f}"
                },
                {
                    "Item Reference": "",
                    "Date": "",
                    "Description": "TOTAL",
                    "Quantity": "",
                    "Unit Cost (RM)": "",
                    "Total Cost (RM)": f"{marketing_cost:.2f}"
                }
            ]

            st.download_button(
                label="📄 Download Proposal/Invoice",
                data=pd.DataFrame(invoice_items).to_csv(index=False),
                file_name=f"veroXis_invoice_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
# Ensure the ownership statement appears at the bottom
footer = st.empty()
footer.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            text-align: center;
            padding: 10px;
            font-size: 12px;
            color: grey;
            border-top: 1px solid #e0e0e0;
        }
    </style>
    <div class="footer">
        <b>Disclaimer:</b> This tool is a proprietary technology owned by <b>ASTRA SOOASANA VENTURES (202403280437 (CA0392873-U))</b>.
        Any access, utilization, or modification of this tool without explicit authorization 
        from the owner is strictly prohibited. All intellectual property rights remain solely with ASTRA SOOASANA VENTURES.
    </div>
""", unsafe_allow_html=True)
