This proposes a "git rebase"/"git rebase interactive" based development workflow for contributors.

## Why git rebase?

It helps to keep project revision history clean and sane. For example, suppose you changed a block of code in your initial patch and submitted that as a pull request, but got a review comment that given block of code should not be changed and it should be done differently. If you just make another commit which puts original lines back, then you just added 2 noise commits to repository, not giving any value, but complicating other people's lives. For example, suppose later it was found that piece of code in question has some issue. Whoever found that, will proceed to investigate why and how it was done, and see those noise commits. And "git blame" will show you as responsible for that code, whereas you didn't really write it!

## Workflow
1. Don't do any work in "master" branch, it belongs to the upstream project. Do any work in topic branches. This isn't really related to "git rebase" workflow, it's part of version control systems best practices at all.
2. Pull upstream changes into your master branch, then propagate to your topic branch using "git rebase master".
3. When you think you've done with implementing the feature, do self-review using "git log -p master..HEAD". Watch for forgotten debug code, re-read commit messages for clarity and typos, etc.
4. If you need to do code changes, do new commits to apply small changes you need (like removing a single line with debug printf()). This better be done one by one, with rebase interactive (next step) after each such auxiliary commit, to not lose track. An alternative way to do this is to use git commit --amend which is essentially equivalent to a git commit followed by git rebase -i to squash the two commits together.
5. Do "git rebase -i master". Your editor will pop up, carefully read instructions. Use "r" action code to edit commit messages, reorder commits and use "f" to apply fix-up commits you created. Be very careful otherwise - it's magic tool, and as any magic, it can do you bad things if you're not considerate. Start slow and careful, you'll get up to speed quickly.
6. Once satisfied, submit a pull request.
7. You may get suggestions for changes, if they're small, treat them as fix-up commits, and repeat from step 4.
8. Re-push your pull request using "git push origin HEAD --force".
9. Repeat from step 7.

## More things to be aware of
1. You can't rebase if you have uncommitted changes, so "git stash save"/"git stash pop" are your best friends.
2. Intuitively, there's slightly more chance to get conflict with rebase than with merge, so apply well-known distributed workflow best practices: a) don't change anything not directly related to the topic you're working on; saw typo? - open up new topic branch from master to fix it, voila. see opportunity for bigger refactor - hold on, leave it for later; b) submit pull requests early, submit pull requests often.

## More questions?
~~~~
git rebase --help
git stash --help
~~~~
Also google it up - there're tons of tutorials, this one tries to be focused and distilled.

## Links

* [“Merge pull request” Considered Harmful](https://blog.spreedly.com/2014/06/24/merge-pull-request-considered-harmful/)

