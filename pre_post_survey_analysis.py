# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import pandas as pd

# %%
def load_data(semester):
    roster = pd.read_csv(f'data/prepost_{semester}_roster.csv')
    predata = pd.read_csv(f'data/prepost_{semester}_predata.csv')
    postdata = pd.read_csv(f'data/prepost_{semester}_postdata.csv')
    # Drop rows where no identifiers were found
    predata = predata[predata['Identifier'].notna()]
    postdata = postdata[postdata['Identifier'].notna()]
    # Keep only the parts of the roster that we need
    roster = roster[['Identifier', 'Degree Type', 'College', 'Student Status', 'Gender']]
    # identifiers = identifiers.set_index('Identifier')
    # predata = predata.set_index('Identifier')
    # postdata = postdata.set_index('Identifier')
    return roster, predata, postdata

def merge(roster, predata, postdata):
    # Add some columns to the data so we can filter things later
    roster['Semester'] = roster['Identifier'].str[0:4]
    predata['prepost'] = 'pre'
    postdata['prepost'] = 'post'
    df = pd.concat([predata, postdata])
    return pd.merge(roster, df, how='right', on='Identifier')

def load_all(semesters):
    df = None
    for semester in semesters:
        if df is None:
            df = merge(*load_data('21sp'))
        else:
            df_additional = merge(*load_data(semester))
            df = pd.concat([df, df_additional], ignore_index=True)
    return df

# %%
semesters = ['21sp', '21fa', '22fa', '23fa']
df_main = load_all(semesters)
print(df_main.shape)
print(df_main.head())
# TODO: Change all of this to just df instead of df1
df = df_main

# %%
# Remove some rows that have known issues
# TODO: Look into the original source to figure out where the problem came from

# Q31 is a numeric question, but the 21fa data contains a string for some reason
sdf = df[df.Q31.notna()]
index = sdf[sdf.Q31 == ' which meant that I was not alone. Moreover I was able to find all the resources available to me at Georgia Tech in one place.'].index.values
df = df.drop(index)
index = sdf[sdf.Q31 == ' I have never planned things on such a long timescale. I cannot over-emphasize how helpful this was.'].index.values
df = df.drop(index)
df


# %%
# Ignore any submissions that had partial submissions
def remove_partial_submissions(df):
    return df[df.Progress == 100]

df = remove_partial_submissions(df)
df

# %% Create a list of the questions for easier access later
questions = [qname for qname in df.columns if qname.startswith('Q')]
non_required_questions = ['Q18_8_TEXT', 'Q24_7_TEXT', 'Q27', 'Q29', 'Q30']
pre_only_questions = ['Q24']
post_only_questions = ['Q26', 'Q27', 'Q28', 'Q29', 'Q30', 'Q31']
multi_select_questions = ['Q23', 'Q24']
required_pre_questions = []
for qname in questions:
    if qname.split('_')[0] in post_only_questions:
        continue
    if qname.split('_')[0] in non_required_questions:
        continue
    if qname in non_required_questions:
        continue
    else:
        required_pre_questions.append(qname)
required_post_questions = []
for qname in questions:
    if qname.split('_')[0] in pre_only_questions:
        continue
    if qname.split('_')[0] in non_required_questions:
        continue
    if qname in non_required_questions:
        continue
    else:
        required_post_questions.append(qname)

# %%
# There are a few questions for which qualtrics does not output questions
# Typically, this is when you select N/A for a question
# Fill in these questions with the appropriate values
for var in questions:
    if var.startswith('Q19_'):
        df.loc[df[var].isna(), var] = 0
    elif var.startswith('Q21_'):
        df.loc[df[var].isna(), var] = 0
    elif var == 'Q23':
        df.loc[df[var].isna(), var] = 6


# %%
# Check if there are any records which claim they are complete but are not
# Qualtrics records "Progress" which should be 100
# But all the required questions should also have answers
# If there are any rows like that, just delete them for now
pre = df.loc[df.prepost == 'pre', required_pre_questions]
drop_these = pre[pre.isna().any(axis=1)].index.values
df = df.drop(drop_these)

post = df.loc[df.prepost == 'post', required_post_questions]
drop_these = post[post.isna().any(axis=1)].index.values
post.loc[drop_these]
df = df.drop(drop_these)
df

# %%
# Reset data types
# Set the numeric coded columns to be ints
# First work on the pre data
integer_questions = [qname for qname in required_pre_questions if qname not in multi_select_questions]
df.loc[df.prepost=='pre', integer_questions] = df.loc[df.prepost=='pre', integer_questions].astype(int)
# Then do the same to the post data
integer_questions = [qname for qname in required_post_questions if qname not in multi_select_questions]
df.loc[df.prepost=='post', integer_questions] = df.loc[df.prepost=='post', integer_questions].astype(int)


# %%
# Ignore submissions that were only pre or only post (not both)
def remove_singular_submissions(df):
    return df.groupby('Identifier').filter(lambda r: 'pre' in r['prepost'].values and 'post' in r['prepost'].values)

df = remove_singular_submissions(df)
df

# %%
# Define the correct answers for the knowledge questions Q1 - 13
answers = {'Q1': 3, 'Q2': 2, 'Q3': 2, 'Q3': 4, 'Q5': 4, 'Q6': 4, 'Q7': 2, 'Q8': 4, 'Q9': 2, 'Q10': 3, 'Q11': 1, 'Q12': 1, 'Q13': 3}
# Now convert the entries in the dataframe to be scores instead of the answers
for qname, ans in answers.items():
    # Add 0 to coerce it to an integer
    df.loc[:, qname] = (df[qname] == ans) + 0
df

# %%
# Q17 talk about resilience and there are 4 sub-questions
# Two of these questions are stated as positives and two as negatives
# So the responses need to be flipped before making inferences
# Running this cell will make it so that a higher response means a positive behavior
# answers['Q17_2'] = 6 - answers['Q17_2']
# answers['Q17_3'] = 6 - answers['Q17_3']

# %%
# Value coding for Q23 (inclusive actions):
# 1: Ask for thoughts/input from a peer or student who isn't speak up or getting called on in a class or meeting
# 2: Ask colleagues, peers, and students for their pronouns
# 3: Use gender neutral language - e.g., avoid using gendered words (guys, dudes, ladies, gentlemen) to addres a group of people
# 4: Stop a colleague or student who interrupts another person and ask the original speaker to finish their thought
# 5: Ask someone to stop making offensive jokes or comments they are sharing during a class or meeting
# 6: None of the above

# %%
# Value coding for Q24 (where did you hear)
# 1: From a friend or colleague in my department/program
# 2: From a friend or colleague in a different department/program
# 3: Email from my school/program
# 4: Email from Office of Graduate Education
# 5: GradIO
# 6: Talked with someone at GradExpo
# 7: Other
# 8: Announcement in the Daily Digest Email
