from django import forms

from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = 'Без группы'

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if '!' not in data:
            raise forms.ValidationError(
                'Поставте в конце восклицательный знак!'
            )
        return data


class CommentForm(forms.ModelForm):

    MIN_COMMENT_LEN = 1

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < self.MIN_COMMENT_LEN:
            raise forms.ValidationError(
                'Длинна комментария не должна быть меньше '
                f'{self.MIN_COMMENT_LEN} символов'
            )
        return data
