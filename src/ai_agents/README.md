# Traditional OCR
- OCR

# New OCR
- VisionTransformer

# Others
- OpenRouter (LLM)
    - 


# High level flow
Image frontend --> Encoded base64 --> backend --> decode --> OCR_1 --> OCR Score (higher) --> OCR Result --> LLM /AI Agent --> Return prompt/ confidence
                                                     |-----> OCR_2 --> OCR Score (lower)