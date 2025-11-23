import gradio as gr


def introduction():
    return gr.HTML(
        """
        <div style="
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        ">
            <!-- Hero Section -->
            <div style="
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                color: white;
                margin-bottom: 30px;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
            ">
                <h1 style="
                    font-size: 3em;
                    margin: 0 0 15px 0;
                    font-weight: 800;
                    letter-spacing: -1px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                ">🎬 Vidzly</h1>
                <p style="
                    font-size: 1.3em;
                    margin: 0 0 15px 0;
                    opacity: 0.95;
                    font-weight: 300;
                ">Transform Raw Footage Into Viral Content</p>
                <p style="
                    font-size: 1em;
                    margin: 0 auto;
                    max-width: 600px;
                    opacity: 0.9;
                    line-height: 1.5;
                ">AI-powered short-form video creation. No editing skills required—just your creativity.</p>
            </div>

            <!-- Features Grid -->
            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            ">
                <div style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 25px 20px;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(245, 87, 108, 0.2);
                ">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🎥</div>
                    <h3 style="margin: 0; font-size: 1.1em;">Upload Clips</h3>
                </div>
                
                <div style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 25px 20px;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(79, 172, 254, 0.2);
                ">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🎨</div>
                    <h3 style="margin: 0; font-size: 1.1em;">Describe Vision</h3>
                </div>
                
                <div style="
                    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 25px 20px;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(67, 233, 123, 0.2);
                ">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">⚡</div>
                    <h3 style="margin: 0; font-size: 1.1em;">AI Processing</h3>
                </div>
                
                <div style="
                    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                    padding: 25px 20px;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(250, 112, 154, 0.2);
                ">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">📱</div>
                    <h3 style="margin: 0; font-size: 1.1em;">Export & Share</h3>
                </div>
            </div>
        </div>
        """
    )
