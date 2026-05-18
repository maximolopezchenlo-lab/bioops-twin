FROM python:3.11-slim

# Create user to run the application (Required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=user:user . .

# Expose the Gradio port
EXPOSE 7860

# Run supervisor to manage both the Proxy and Gradio processes
CMD ["supervisord", "-c", "supervisord.conf"]
