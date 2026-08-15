import gradio as gr
from rose.scorer_hash import RoSE
import penman

# Sample examples for 1-click testing
EXAMPLES = [
    [
        "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        3,
        0.99
    ],
    [
        "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "(c / chase-01\n   :ARG0 (ct / cat)\n   :ARG1 (d / dog))",
        3,
        0.99
    ],
    [
        "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "(d / dog\n   :ARG0-of (c / chase-01\n      :ARG1 (ct / cat)))",
        3,
        0.99
    ],
]

def evaluate_amr(ref_str, hyp_str, n_iter, tau):
    if not ref_str.strip() or not hyp_str.strip():
        return "<div style='color: red; padding: 10px;'>⚠️ Vui lòng nhập đầy đủ cả Reference AMR và Hypothesis AMR!</div>", "", "Vui lòng nhập AMR"
    
    # Check syntax validation with penman
    try:
        ref_graph = penman.loads(ref_str)
    except Exception as e:
        return f"<div style='color: red; padding: 10px;'>❌ Lỗi cú pháp trong Reference AMR:<br><code>{str(e)}</code></div>", "", "Lỗi cú pháp Reference"
        
    try:
        hyp_graph = penman.loads(hyp_str)
    except Exception as e:
        return f"<div style='color: red; padding: 10px;'>❌ Lỗi cú pháp trong Hypothesis AMR:<br><code>{str(e)}</code></div>", "", "Lỗi cú pháp Hypothesis"
    
    try:
        scorer = RoSE(num_iterations=int(n_iter), similarity_threshold_tau=float(tau))
        score_dict = scorer.compute_from_string(ref_str, hyp_str)
        
        metric_name = scorer.name()
        score_val = score_dict.get(metric_name, 0.0)
        
        # Color badge depending on score
        if score_val >= 0.8:
            color = "#10B981" # Green
            verdict = "Rất tương đồng / Đồng nghĩa (High Similarity)"
        elif score_val >= 0.4:
            color = "#F59E0B" # Yellow/Orange
            verdict = "Tương đồng một phần (Moderate Similarity)"
        else:
            color = "#EF4444" # Red
            verdict = "Khác biệt ý nghĩa / Khác vai trò ngữ nghĩa (Low Similarity)"
            
        score_html = f"""
        <div style="background-color: #1f2937; border-radius: 12px; padding: 25px; text-align: center; color: white; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <h3 style="margin:0; color: #9CA3AF; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em;">ĐIỂM ĐỘ TƯƠNG ĐỒNG SEMCAT / RoSE ({metric_name})</h3>
            <h1 style="font-size: 3.5rem; margin: 15px 0; color: {color}; font-weight: 800;">{score_val:.4f}</h1>
            <span style="background-color: {color}22; border: 1px solid {color}; color: {color}; padding: 6px 16px; border-radius: 20px; font-size: 1rem; font-weight: 600; display: inline-block;">{verdict}</span>
        </div>
        """
        
        details_md = f"""
        ### 📊 Chi tiết tham số & Cấu hình đánh giá:
        * **Thuật toán cốt lõi:** Weisfeiler-Leman (WL) Subgraph Hashing + Graph Standardization
        * **Số vòng lặp WL ($N$):** `{n_iter}`
        * **Ngưỡng tương đồng ($\\\\tau$):** `{tau}`
        * **Số câu Reference:** `{len(ref_graph)}`
        * **Số câu Hypothesis:** `{len(hyp_graph)}`
        """
        
        return score_html, details_md, "✅ Đã tính toán thành công!"
        
    except Exception as e:
        return f"<div style='color: red; padding: 10px;'>❌ Lỗi trong quá trình tính toán:<br><code>{str(e)}</code></div>", "", "Lỗi tính toán"

# Build Gradio UI
with gr.Blocks(title="SEMCAT / RoSE - AMR Similarity Evaluator", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🧠 SEMCAT / RoSE: Web UI Đánh giá Độ tương đồng Ngữ nghĩa AMR
        > **Dựa trên Bài báo:** *Semantic evaluation metric conforming to AMR theory (SEMCAT)* (2026)
        > 
        > Giao diện đánh giá độ tương đồng cấu trúc logic điều kiện đúng (Truth-Conditional Semantics) giữa 2 đồ thị AMR.
        """
    )
    
    with gr.Row():
        with gr.Column():
            ref_input = gr.Textbox(
                lines=7, 
                placeholder="Nhập Reference AMR (PENMAN notation)...", 
                label="1. Reference AMR (Đồ thị gốc)"
            )
        with gr.Column():
            hyp_input = gr.Textbox(
                lines=7, 
                placeholder="Nhập Hypothesis AMR (PENMAN notation)...", 
                label="2. Hypothesis AMR (Đồ thị so sánh)"
            )
            
    with gr.Accordion("⚙️ Cấu hình Tham số (Hyperparameters)", open=False):
        with gr.Row():
            n_iter_slider = gr.Slider(minimum=2, maximum=10, step=1, value=3, label="Số vòng lặp WL (N)")
            tau_slider = gr.Slider(minimum=0.5, maximum=0.99, step=0.01, value=0.99, label="Ngưỡng Tau (τ)")
            
    btn = gr.Button("🚀 Tính toán Độ tương đồng (Evaluate)", variant="primary", size="lg")
    
    with gr.Row():
        output_html = gr.HTML(label="Kết quả điểm số")
    
    output_md = gr.Markdown()
    status_box = gr.Textbox(label="Trạng thái", interactive=False)
    
    gr.Markdown("--- \n### 💡 Mẫu thử nghiệm nhanh (Click để load dữ liệu):")
    gr.Examples(
        examples=EXAMPLES,
        inputs=[ref_input, hyp_input, n_iter_slider, tau_slider],
        outputs=[output_html, output_md, status_box],
        fn=evaluate_amr,
        cache_examples=False
    )
    
    btn.click(
        fn=evaluate_amr,
        inputs=[ref_input, hyp_input, n_iter_slider, tau_slider],
        outputs=[output_html, output_md, status_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
