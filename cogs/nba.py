import discord
import asyncio
from discord.ext import commands
from nba_api.stats.endpoints import scoreboard
from nba_api.stats.static import teams
import pandas as pd

class nba(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("nba is ready to go")

    @commands.command()
    async def scores(self, ctx, *, date=''):
        # TODO: handle special games (All-Star)
        result = ''
        if date != '':
            try:
                score = scoreboard.Scoreboard(game_date=date)
                result = await self.get_scores(score)
            except:
                result = 'Invalid date format, make sure the format is "YYYY-MM-DD" '
        else:
            score = scoreboard.Scoreboard()
            result = await self.get_scores(score)
        await ctx.send(result)

    async def get_scores(self, score):
        result = ''
        line_score = score.line_score
        ls_df = line_score.get_data_frame()
        if ls_df.empty:
            result = 'No games were played that day'
        else:
            team_points = ls_df[['TEAM_ID', 'PTS']]
            for x in range(0, len(team_points), 2):
                try:
                    away_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x])['full_name']
                    home_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x + 1])['full_name']
                # handles case where teams are not in the list of current teams i.e. Team LeBron, West All-Stars
                except:
                    away_team = ls_df['TEAM_CITY_NAME'][x] + ' ' + ls_df['TEAM_ABBREVIATION'][x]
                    home_team = ls_df['TEAM_CITY_NAME'][x + 1] + ' ' + ls_df['TEAM_ABBREVIATION'][x+1]
                away_points = ls_df['PTS'][x]
                home_points = ls_df['PTS'][x + 1]
                away_win = ''
                home_win = ''
                if home_points > away_points:
                    home_win = '**'
                else:
                    away_win = '**'
                result += '{}{}  {}{} - {}{}  {}{}\n'.format(away_win,
                                                             away_team,
                                                             away_points, away_win, home_win, home_points,
                                                             home_team,
                                                             home_win)
        return result

def setup(client):
    client.add_cog(nba(client))