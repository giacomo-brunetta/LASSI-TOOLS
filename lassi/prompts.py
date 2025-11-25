from lassi.compiler import Language, Compiler
from enum import Enum
import json


# =============================================================================
# System Prompts
# =============================================================================

def get_sysyem_prompt(lang : Language = Language.C, context = True, optimize_energy: bool = False):
    with open('lassi/prompt_dicts/system_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        vars = {'lang': lang.value}
        key = "general_system" 
        key += "_nocontext" if not context else ""
        key += "_ee" if optimize_energy else ""

        return prompt_dict[key].format(**vars)

# =============================================================================
# Refactoring Prompts
# =============================================================================
        
def get_refactoring_baseline(lang : Language = Language.C, parallel : bool = False):
    with open('lassi/prompt_dicts/refactoring_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "baseline_nocontext" 
        key += "_parallel" if parallel else "_serial"

        vars = {'lang': lang.value}

        return prompt_dict[key].format(**vars)
    
def get_refactoring_plan(parallel : bool = False):
    with open('lassi/prompt_dicts/refactoring_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "refactorplan" 
        key += "_parallel" if parallel else "_serial"

        return prompt_dict[key]
    
def get_refactor_prompt(lang : Language = Language.C, parallel : bool = False):
    with open('lassi/prompt_dicts/refactoring_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "refactor" 
        key += "_parallel" if parallel else "_serial"

        vars = {
            'lang': lang.value,
            'compiler' : Compiler.from_language(lang).value
            }

        return prompt_dict[key].format(**vars)
    
def get_refactor_iteration_prompt(lang : Language = Language.C, parallel : bool = False):
    with open('lassi/prompt_dicts/refactoring_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "refactor_iteration" 
        key += "_parallel" if parallel else "_serial"

        vars = {
            'lang': lang.value,
            'compiler' : Compiler.from_language(lang).value
            }

        return prompt_dict[key].format(**vars)
    
# =============================================================================
# Error Correction Prompt
# =============================================================================

def get_error_correction_prompt():
    with open('lassi/prompt_dicts/correction_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "error" 

        return prompt_dict[key]
    
# =============================================================================
# Code Comparison Prompt
# =============================================================================

def get_comparison_prompt(lang : Language = Language.C, parallel : bool = False):
    with open('lassi/prompt_dicts/comparison_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "comparison"
        key += "_parallel" if parallel else "_serial"

        vars = {'lang': lang.value}

        return prompt_dict[key].format(**vars)
    
# =============================================================================
# Analysis Prompt
# =============================================================================

def get_comparison_prompt(lang : Language = Language.C, parallel : bool = False):
    with open('lassi/prompt_dicts/code_analysis_prompts.json', 'r', encoding='utf-8') as f:
        prompt_dict = json.load(f)

        key = "analysis"
        key += "_parallel" if parallel else "_serial"

        vars = {'lang': lang.value}

        return prompt_dict[key].format(**vars)