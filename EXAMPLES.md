# Example Workflows

This document provides example workflows showing how to effectively use ComfyUI Violet Tools nodes in your image generation pipeline.

## Basic Aesthetic Workflow

This workflow demonstrates the core functionality of connecting multiple Violet Tools nodes:

```
[Load Checkpoint] → [CLIP Text Encode]
                         ↑
[Quality Queen] → [Aesthetic Alchemist] → [Glamour Goddess] → [Encoding Enchantress] → [Positive Conditioning]
                                                                        ↓
[Negativity Nullifier] → [Encoding Enchantress] → [Negative Conditioning]
```

### Setup Steps:
1. **Quality Queen**: Enable boilerplate, select "Random" style
2. **Aesthetic Alchemist**: Choose "Gothic Glam" + "Cyberpunk", strengths 1.2 and 0.8
3. **Glamour Goddess**: Set hair to "Random", makeup to "Random"
4. **Negativity Nullifier**: Use default settings
5. **Encoding Enchantress**: Connect all positive outputs to this node
6. Connect to your sampler as usual

## Character-Focused Workflow

For detailed character generation with precise control:

```
[Base Prompt] → [Body Bard] → [Pose Priestess] → [Glamour Goddess] → [Encoding Enchantress]
                                                                            ↓
                                                                    [Conditioning]
```

### Character Example Settings:
- **Body Bard**: Select specific body features and proportions
- **Pose Priestess**: Choose "confident pose" or "seductive pose"
- **Glamour Goddess**: Hair: "long flowing hair", Makeup: "bold eyeliner"

## Style Experimentation Workflow

Perfect for exploring different aesthetic combinations:

```
[Aesthetic Alchemist #1] → [Encoding Enchantress] → [Conditioning A]
[Aesthetic Alchemist #2] → [Encoding Enchantress] → [Conditioning B]

Use ConditioningAverage or ConditioningConcat to blend results
```

## Tips for Best Results

### Strength Settings
- **Conservative blending**: 0.7-1.0 strength values
- **Bold experimentation**: 1.2-1.8 strength values
- **Subtle hints**: 0.3-0.6 strength values

### Aesthetic Combinations That Work Well
- **Gothic Glam** + **Dark Academia** = Sophisticated dark elegance
- **Cyberpunk** + **Nu-Goth** = Futuristic alternative style
- **Cottagecore** + **Fairycore** = Whimsical natural beauty
- **Y2K** + **E-girl** = Nostalgic digital culture

### Random Generation Tips
- Use "Random" selections for inspiration and happy accidents
- Save successful random combinations by noting the generated styles
- Mix random and manual selections for controlled variety

## Advanced Techniques

### Conditional Styling
Use multiple Aesthetic Alchemist nodes with different settings, then use ComfyUI's conditioning nodes to apply them conditionally based on your needs.

### Prompt Weighting
The nodes automatically handle prompt weighting syntax, but you can add additional emphasis using parentheses in the "extra" fields.

### Batch Generation
Set up workflows with random selections to generate varied results in batch processing for style exploration.
